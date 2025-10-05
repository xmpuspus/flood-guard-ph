import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/api/chat")
async def chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat"""
    await websocket.accept()

    try:
        # Get LLM service from app state
        llm_service: LLMService = websocket.app.state.llm_service

        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message = message_data.get("message", "")
            session_id = message_data.get("session_id", "default")
            anthropic_key = message_data.get("anthropic_key")
            openai_key = message_data.get("openai_key")

            if not message:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Message is required",
                    }
                )
                continue

            if not anthropic_key or not openai_key:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "API keys are required. Please configure them in Settings.",
                    }
                )
                continue

            # Process message and stream responses with user's API keys
            async for response in llm_service.chat(message, session_id, anthropic_key, openai_key):
                await websocket.send_json(response)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "content": str(e),
                }
            )
        except:
            pass