import chromadb
from chromadb import Settings
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

class RAG:
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3.1:8b"
        )
        self.embeddings = OllamaEmbeddings(model="embeddinggemma")

        self.vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=self.embeddings,
            client=chromadb.HttpClient(host="http://chromadb:8000"),
        )
        print(self.vector_store._collection.count())
