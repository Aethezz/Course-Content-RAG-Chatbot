
## ⚙️ Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd chatbot-project
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(If using Ollama)** **Install Ollama:**
    *   Download and install Ollama from [https://ollama.com/](https://ollama.com/).
    *   Ensure the Ollama application/service is running in the background.
    *   Pull the desired model(s) via terminal:
        ```bash
        ollama pull llama3:8b # Or mistral, phi3:mini, etc. - match your .env config
        ```

## 🔧 Configuration

1.  **Create `.env` file:** Copy the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit `.env` file:** Open the `.env` file in a text editor and configure the variables:
    *   **`LLM_MODEL_NAME`**:
        *   If using **Ollama**: Set this to the exact model name you pulled (e.g., `llama3:8b`, `mistral`, `phi3:mini`).
        *   If using **Gemini**: Set this to a valid Gemini model ID (e.g., `gemini-1.5-flash-latest`, `gemini-1.0-pro`).
    *   **`GOOGLE_API_KEY`**: (Required **only** if using Gemini) Paste your API key obtained from [Google AI Studio](https://aistudio.google.com/).
    *   **`EMBEDDING_MODEL_NAME`**: Defaults to `all-MiniLM-L6-v2`. You can change this if needed, but ensure it's compatible with Sentence Transformers/HuggingFaceEmbeddings.
    *   **`OLLAMA_BASE_URL`**: (Optional, only for Ollama) Uncomment and change if your Ollama service runs on a different URL than the default `http://localhost:11434`.
    *   **Other Variables**: Review `VECTOR_STORE_PATH`, `CHROMA_COLLECTION_NAME`, `CHUNK_SIZE`, etc., and adjust if necessary.

    **IMPORTANT:** Do **not** commit your `.env` file to version control. Add it to your `.gitignore` file if it's not already there.

## ▶️ Running the Application

**Choose ONE method based on your configured LLM:**

**Method A: Using Google Gemini**

1.  Ensure your `GOOGLE_API_KEY` and Gemini `LLM_MODEL_NAME` are set correctly in `.env`.
2.  Run the FastAPI application using Uvicorn:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *(Use `--reload` for development; remove it for production)*

**Method B: Using Ollama**

1.  Ensure the Ollama application/service is running in the background on your system.
2.  Ensure the `LLM_MODEL_NAME` in your `.env` file matches a model you have pulled with `ollama pull <model_name>`.
3.  Ensure `GOOGLE_API_KEY` is **not** needed/set in `.env` (or remove the check in the code if you keep both possibilities).
4.  Run the FastAPI application using Uvicorn:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *(Use `--reload` for development; remove it for production)*

## 🚀 Usage

1.  **Access the Application:** Open your web browser and navigate to `http://localhost:8000` (or the host/port you configured).
2.  **Toggle Theme (Optional):** Use the sun/moon icon in the top-right corner to switch between light and dark modes.
3.  **Upload Documents:**
    *   Click the "+" icon button near the message input field.
    *   Select "Upload File" from the pop-up menu.
    *   Choose a `.pdf`, `.docx`, `.txt`, or `.md` file.
    *   A status message will appear indicating uploading and processing. Processing happens in the background and may take some time depending on file size.
4.  **Chat:**
    *   Once processing is complete (you might need to wait a bit), type your questions related to the content of the uploaded document(s) into the message input area.
    *   Press Enter (or click the Send button).
    *   The AI Assistant will retrieve relevant context and generate an answer based on the documents. Formulas should be rendered using KaTeX.

## 🔮 Future Improvements (TODO)

*   [ ] Add user authentication.
*   [ ] Store chat history per user.
*   [ ] Implement streaming responses from the LLM for better perceived performance.
*   [ ] More robust error handling for document processing.
*   [ ] Add ability to manage/delete uploaded documents and their vectors.
*   [ ] Use Celery/Redis for more robust background task processing.
*   [ ] Improve prompt engineering for different query types.
*   [ ] Add unit and integration tests.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue. (Add more specific guidelines if desired).

## 📜 License

This project is licensed under the MIT License - see the LICENSE file (if created) for details.