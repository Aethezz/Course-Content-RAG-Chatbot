import asyncio
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler # For console streaming
from langchain.callbacks.base import AsyncCallbackHandler # For WebSocket streaming (more advanced)

from app.core.config import settings
from app.core.vector_store import get_vector_store


print(f"Initializing ChatGoogleGenerativeAI with model: {settings.LLM_MODEL_NAME}")
# --- Initialize LLM ---
try:
    # LangChain automatically uses GOOGLE_API_KEY from environment
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        temperature=0.7,
        convert_system_message_to_human=True # Often needed for Gemini compatibility with generic prompts
    )
    print("ChatGoogleGenerativeAI initialized.")
    # Optional: Test call (check quotas)
    # try:
    #     print("Testing Gemini connection...")
    #     llm.invoke("Hello!")
    #     print("Gemini connection test successful.")
    # except Exception as test_e:
    #     print(f"!!! Warning: Gemini connection test failed: {test_e}")
except Exception as e:
    print(f"!!! Error initializing ChatGoogleGenerativeAI: {e}")
    print("!!! Ensure 'GOOGLE_API_KEY' is set correctly in .env and the model name is valid.")
    llm = None # Or raise error

# --- Define Custom Prompt (Optional but Recommended) ---
prompt_template = """Use the following context from the course materials to answer the user's question.
If the context doesn’t provide a clear answer, state that you don’t know and do not attempt to make up an answer.
If additional relevant information from the context can help, feel free to include it to provide a more complete response.
Ensure your answer is concise, clear, and informative."

**Formatting Instructions:**
- When presenting mathematical formulas or equations, enclose them in LaTeX syntax.
- For inline formulas (within a sentence), use single dollar signs: $formula$.
- For display formulas (on their own line, centered), use double dollar signs: $$formula$$.
- Ensure standard LaTeX formatting for symbols (e.g., \int, \sum, \delta, \tau, \infty).
- Separating all formulas from regular text with appropriate spacing.
- Preserving the original sentence structure and content.

Context:
{context}

Question: {question}

Answer:"""

QA_PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)


# --- Build RetrievalQA Chain ---
def get_qa_chain():
    if llm is None: # Check LLM init
         print("!!! Cannot create QA chain: LLM not initialized.")
         return None
    vector_db = get_vector_store()
    retriever = vector_db.as_retriever(
        search_type="similarity", # Or "mmr" for Maximal Marginal Relevance
        search_kwargs={"k": settings.RETRIEVED_DOCS_COUNT} # Number of chunks to retrieve
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "stuff": Puts all context in the prompt (simplest, works for small contexts)
                             # Other types: "map_reduce", "refine", "map_rerank" for larger contexts
        retriever=retriever,
        return_source_documents=True,  # Optional: Return which chunks were used
        chain_type_kwargs={"prompt": QA_PROMPT} # Use our custom prompt
    )
    return qa_chain

# --- Store the chain globally (or use Depends in FastAPI) ---
qa_chain_instance = get_qa_chain()


# In app/services/chatbot_service.py

async def get_bot_response(user_message: str) -> str:
    """Generates a response using the RAG pipeline."""
    print(f"\n--- RAG Start ---") # Mark start
    print(f"Received query: {user_message}")
    if not qa_chain_instance:
        print("!!! Error: QA Chain not initialized.")
        return "Error: QA Chain not initialized."
    if not settings.GOOGLE_API_KEY or "your_openai_api_key_here" in settings.GOOGLE_API_KEY:
         print("!!! Error: GOOGLE API Key not configured.")
         return "Error: GOOGLE API Key not configured. Cannot generate response."

    try:
        print(">>> Calling qa_chain_instance.ainvoke...")
        # Use await for the async invocation
        response = await qa_chain_instance.ainvoke({"query": user_message})
        print("<<< qa_chain_instance.ainvoke completed.") # Check if it gets past this

        answer = response.get("result", None) # Get result or None
        source_docs = response.get("source_documents", [])

        print(f"Retrieved {len(source_docs)} source documents.")
        # Log sources if needed for debugging context length
        # for i, doc in enumerate(source_docs):
        #     print(f"  Source {i+1}: {doc.metadata.get('source', 'N/A')} (Len: {len(doc.page_content)})")

        if answer:
            print(f"Generated Answer: {answer[:200]}...") # Log partial answer
            print("--- RAG End (Success) ---")
            return answer
        else:
            print("!!! Error: No 'result' key found in LLM response.")
            print(f"Full Response Received: {response}") # Log the raw response
            print("--- RAG End (Failure: No Result) ---")
            return "Sorry, I received a response but couldn't extract the answer."

    except Exception as e:
        print(f"!!! Error during RAG pipeline execution: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback
        print("--- RAG End (Failure: Exception) ---")
        # Provide a more informative error message if possible
        error_type = type(e).__name__
        return f"Sorry, an error occurred ({error_type}). Please check server logs."