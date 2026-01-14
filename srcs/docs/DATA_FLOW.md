1. File Upload Flow
* User uploads a non-structured file via the frontend.
* Frontend sends the file to the backend, and if necessary converts them to text representation.
* Backend stores the file in persistent storage.
* Backend triggers the embedding pipeline.
* Pipeline extracts text and generates embeddings.
* Embeddings are stored in the vector database.
* Backend updates metadata so the file appears in the admin UI.

2. RAG Query Flow
* User enters a query in the frontend.
* Frontend sends the query to the backend.
* Backend forwards the query to the Ollama agent.
* Ollama evaluates whether a RAG lookup is needed.
* If needed, Ollama requests document embeddings from the vector database.
* Vector DB returns top-K relevant document chunks.
* Ollama uses retrieved context to create a final response.
*  Backend sends the answer back to the frontend.

3. Administration Flow (Regions, Schools, Files)
* User performs management action in the frontend (add/edit/delete).
* Frontend sends API request to backend.
* Backend performs DB updates and returns the updated state.
* Frontend refreshes the UI to show updated administration data.

4. View Uploaded Files Flow
* Frontend requests list of uploaded files from backend.
* Backend fetches file metadata from persistent storage or database.
* Backend returns file list to frontend.
* User can download or view file details. (edited) 