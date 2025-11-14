from dataclasses import dataclass

import anyio
import chromadb
from langchain.agents import create_agent
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.tools import tool

from chat.prompts import agent_system_prompt

@dataclass
class ModelResponse:
    role: str
    content: int

class RAG:
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3.1:8b"
        )
        self.embeddings = OllamaEmbeddings(model="embeddinggemma", base_url="http://host.docker.internal:11434")

        self.vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=self.embeddings,
            persist_directory="/app/src/chromdb_dir"

            # client=chromadb.HttpClient(host="http://localhost:8000"),
            # client_settings=chromadb.Settings(chroma_api_impl="chromadb.api.fastapi.FastAPI")
        )
        # self.vector_store = Chroma(
        #     collection_name="example_collection",
        #     embedding_function=self.embeddings,
        #     persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
        # )
        print(f"Current documents in ChromaDb: # {self.vector_store._collection.count()}")

    def add_document(self, path: str):
        loader = UnstructuredWordDocumentLoader(file_path=path)
        docs = loader.load()
        assert len(docs) == 1
        print(f"Total characters: {len(docs[0].page_content)}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents(docs)
        print(f"Split blog post into {len(all_splits)} sub-documents.")

        # res = self.vector_store.add_documents(documents=all_splits)
        # print("Added document", res[0])

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

