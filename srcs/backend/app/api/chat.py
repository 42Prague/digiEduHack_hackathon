

from fastapi import APIRouter

from chat.RAG import RAG

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.get("/")
def read_root():
    rag = RAG()
    return {"Hello": "aaa"}