from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.llm_service import LLMService
from tools.appointment_tools import AppointmentTools
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    tool_calls: List[Dict] = []
    tool_results: List[Dict] = []
    session_id: Optional[str] = None


async def execute_tool(tool_name: str, tool_args: Dict, db: AsyncSession) -> Dict:
    """Execute a tool by name with provided arguments."""
    tools = AppointmentTools()

    tool_map = {
        "identify_user": lambda args: AppointmentTools.identify_user(db=db, **args),
        "fetch_slots": lambda args: AppointmentTools.fetch_slots(db=db, **args),
        "book_appointment": lambda args: AppointmentTools.book_appointment(db=db, **args),
        "retrieve_appointments": lambda args: AppointmentTools.retrieve_appointments(db=db, **args),
        "cancel_appointment": lambda args: AppointmentTools.cancel_appointment(db=db, **args),
        "modify_appointment": lambda args: AppointmentTools.modify_appointment(db=db, **args),
        "end_conversation": lambda args: AppointmentTools.end_conversation(db=db, **args),
    }

    if tool_name not in tool_map:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    try:
        result = await tool_map[tool_name](tool_args)
        return result
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {"success": False, "error": str(e)}


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Process a chat message with tool calling support."""
    llm = LLMService()
    tool_calls_log = []
    tool_results_log = []

    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        response_message = await llm.chat(messages=messages, tools=True)
        messages.append(response_message)

        # Handle tool calls
        max_iterations = 5
        iteration = 0
        while response_message.get("tool_calls") and iteration < max_iterations:
            iteration += 1
            tool_results = []

            for tc in response_message["tool_calls"]:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])

                tool_calls_log.append({"name": tool_name, "args": tool_args})

                result = await execute_tool(tool_name, tool_args, db)
                tool_results_log.append({"name": tool_name, "result": result})

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result),
                })

            messages.extend(tool_results)
            response_message = await llm.chat(messages=messages, tools=True)
            messages.append(response_message)

        final_content = response_message.get("content", "I'm here to help. How can I assist you?")

        return ChatResponse(
            message=final_content,
            tool_calls=tool_calls_log,
            tool_results=tool_results_log,
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await llm.close()


@router.post("/summary")
async def generate_summary(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Generate a call summary from conversation history."""
    llm = LLMService()
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        summary_json = await llm.generate_summary(messages, [])
        try:
            summary_data = json.loads(summary_json)
        except Exception:
            summary_data = {"summary": summary_json, "appointments": [], "key_points": []}
        return summary_data
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await llm.close()


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for real-time chat with tool calling."""
    await websocket.accept()
    llm = LLMService()
    conversation_history = []

    try:
        # Send welcome
        await websocket.send_json({
            "type": "message",
            "role": "assistant",
            "content": "Hello! Welcome to Mykare Healthcare. I'm your AI assistant. May I have your phone number to get started?",
        })

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_message = payload.get("content", "")

            conversation_history.append({"role": "user", "content": user_message})

            await websocket.send_json({"type": "thinking"})

            response_message = await llm.chat(messages=conversation_history, tools=True)
            conversation_history.append(response_message)

            max_iterations = 5
            iteration = 0
            while response_message.get("tool_calls") and iteration < max_iterations:
                iteration += 1
                tool_results = []

                for tc in response_message["tool_calls"]:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])

                    await websocket.send_json({
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "status": "running",
                    })

                    result = await execute_tool(tool_name, tool_args, db)

                    await websocket.send_json({
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "result": result,
                        "status": "completed",
                    })

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result),
                    })

                conversation_history.extend(tool_results)
                response_message = await llm.chat(messages=conversation_history, tools=True)
                conversation_history.append(response_message)

            final_content = response_message.get("content", "How else can I help you?")
            conversation_history[-1] = {"role": "assistant", "content": final_content}

            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": final_content,
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        await llm.close()
