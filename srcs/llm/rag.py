from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore


llm = ChatOllama(
    model="llama3.1:8b"
)
embeddings = OllamaEmbeddings(model="embeddinggemma")
vector_store = InMemoryVectorStore(embeddings)




from langchain_community.document_loaders import UnstructuredWordDocumentLoader
loader = UnstructuredWordDocumentLoader(file_path="../../data/Prepis_FG_PedagogLidr_mentori.docx")
docs = loader.load()
assert len(docs) == 1
print(f"Total characters: {len(docs[0].page_content)}")



from langchain_text_splitters import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)
all_splits = text_splitter.split_documents(docs)
print(f"Split blog post into {len(all_splits)} sub-documents.")



document_ids = vector_store.add_documents(documents=all_splits)
print(document_ids[:3])




