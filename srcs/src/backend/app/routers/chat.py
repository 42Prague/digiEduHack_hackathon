from dataclasses import asdict

import anyio
from fastapi import APIRouter
from starlette.websockets import WebSocketDisconnect

from fastapi import WebSocket

from ..chat.RAG import RAG

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

rag = RAG()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # optional: wait for a message to trigger inference
            data = await websocket.receive_text()
            query = data.strip()
            print("Answering query", query)

            # Run inference and stream result
            async for chunk in rag.inference(query):
                print("Sending chunk", chunk)
                await websocket.send_json(asdict(chunk))

            # Signal end of response
            await websocket.send_json({"event": "done"})

    except WebSocketDisconnect:
        pass