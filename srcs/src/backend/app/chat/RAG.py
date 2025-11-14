import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import anyio
import chromadb
from langchain.agents import create_agent
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredPDFLoader, \
    UnstructuredExcelLoader, UnstructuredMarkdownLoader, TextLoader, UnstructuredFileLoader
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.tools import tool

from .prompts import agent_system_prompt
from ..models import School

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma")

@dataclass
class ModelResponse:
    role: str
    content: str

class RAG:
    def __init__(self):
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_HOST
        )
        self.embeddings = OllamaEmbeddings(
            model=OLLAMA_EMBED_MODEL,
            base_url=OLLAMA_HOST
        )

        self.vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=self.embeddings,
            client=chromadb.HttpClient(host="http://chromadb:8000"),
            client_settings=chromadb.Settings(chroma_api_impl="chromadb.api.fastapi.FastAPI")
        )
        print(f"Current documents in ChromaDb: # {self.vector_store._collection.count()}")

    def load_any_document(self, path: str, filename: str):
        ext = Path(filename).suffix.lower()
        print(f"Loading {ext} from {path}")

        loader_map = {
            ".pdf": UnstructuredPDFLoader,
            ".docx": UnstructuredWordDocumentLoader,
            ".doc": UnstructuredWordDocumentLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".xls": UnstructuredExcelLoader,
            ".md": UnstructuredMarkdownLoader,
            ".txt": TextLoader,
        }

        loader_cls = loader_map.get(ext)
        if loader_cls is None:
            return None

        loader = loader_cls(path)
        return loader.load()

    def add_document(self, path: str, filename: str, school: School, uploaded_at: datetime):
        print(f"Adding document: {path}")
        docs = self.load_any_document(path, filename)
        if docs is None:
            print("Error, not supported file type")
            return None
        assert len(docs) == 1
        doc = docs[0]
        doc.metadata.update({
            "timestamp": uploaded_at.isoformat(),
            "filename": filename,
            "school_name": school.name,
            "region_name": school.region.name,
        })
        print(doc.metadata)
        print(f"Total characters: {len(doc.page_content)}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents(docs)
        print(f"Split blog post into {len(all_splits)} sub-documents.")

        res = self.vector_store.add_documents(all_splits)
        print(f"Added {len(res)} sub-documents.")


    def _retrieve_context(self, query: str):
        retrieved_docs = self.vector_store.similarity_search(query, k=2)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    async def inference(self, query: str):
        @tool(response_format="content_and_artifact")
        def retrieve_context(query: str):
            """Retrieve information to help answer a query."""
            return self._retrieve_context(query)

        agent = create_agent(self.llm, [retrieve_context], system_prompt=agent_system_prompt)
        async for token, metadata in agent.astream(
                {"messages": [{"role": "user", "content": query}]},
                stream_mode="messages",
        ):
            print("Node received")
            node = metadata['langgraph_node']
            if len(token.content_blocks) > 0:
                content = token.content_blocks[0]
                type = content["type"] if "type" in content else None
                if type is None:
                    continue

                if type == "text":
                    print("Yielding response")
                    yield ModelResponse(role=node, content=content['text'])
