"""Chatbot API endpoints for handling chat interactions.

This module provides endpoints for chat interactions, including regular chat,
message history management, and chat history clearing.
"""

from typing import AsyncGenerator, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse

from app.api.v1.auth import get_current_session
from app.core.agno.graph import AgnoAgent
from app.core.config import settings
from app.core.dependencies import DatabaseServiceDep, MessageServiceDep
from app.core.limiter import limiter
from app.core.logging import logger
from app.domain.entities.message_entity import MessageRole, MessageStatus
from app.models.session import Session
from app.schemas.chat import (
    ChatExportRequest,
    ChatExportResponse,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatInsightsResponse,
    ChatMetrics,
    ChatRequest,
    ChatResponse,
    ChatSearchRequest,
    ChatSearchResult,
    StreamResponse,
)
from app.shared.constants.http import CONTENT_TYPE_SSE

router = APIRouter()
agent = AgnoAgent()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
    message_service: MessageServiceDep = None,
):
    """Process a chat request using Agno with proper message management.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session: The current session from the auth token.
        message_service: Message service for business logic.

    Returns:
        ChatResponse: The processed chat response.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    import time

    try:
        logger.info(
            "chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        # Get the last user message from the request
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")

        last_user_message = user_messages[-1]

        # Store user message in Firebase
        user_message_entity = await message_service.create_user_message(
            session_id=session.id,
            user_id=session.user_id,
            content=last_user_message.content,
        )

        logger.info(
            "user_message_stored",
            session_id=session.id,
            message_id=user_message_entity.id,
        )

        # Measure processing time
        start_time = time.time()

        # Get AI response
        result = await agent.get_response(
            chat_request.messages, session.id, user_id=session.user_id
        )

        processing_time = time.time() - start_time

        # Store assistant message(s) in Firebase
        assistant_messages = [msg for msg in result if msg.role == "assistant"]
        stored_messages = []

        for assistant_msg in assistant_messages:
            # Extract token count from the message content (approximation)
            tokens_used = len(assistant_msg.content.split()) * 1.3  # Rough estimate
            
            assistant_message_entity = await message_service.create_assistant_message(
                session_id=session.id,
                user_id=session.user_id,
                content=assistant_msg.content,
                model_used=settings.LLM_MODEL,
                tokens_used=int(tokens_used),
                processing_time=processing_time,
                confidence_score=0.9,  # Default confidence
            )
            
            stored_messages.append(assistant_message_entity)

            logger.info(
                "assistant_message_stored",
                session_id=session.id,
                message_id=assistant_message_entity.id,
                tokens_used=int(tokens_used),
            )

        logger.info(
            "chat_request_processed",
            session_id=session.id,
            user_message_id=user_message_entity.id,
            assistant_messages_count=len(stored_messages),
        )

        return ChatResponse(messages=result)
    except Exception as e:
        logger.error(
            "chat_request_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_CHAT_STREAM)
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
    message_service: MessageServiceDep = None,
):
    """Process a chat request with streaming response using Agno.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session: The current session from the auth token.
        message_service: Message service for business logic.

    Returns:
        StreamingResponse: Server-sent events stream with chat tokens.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    import json
    import time

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(
                "chat_stream_request_received",
                session_id=session.id,
                message_count=len(chat_request.messages),
            )

            # Get the last user message from the request
            user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
            if not user_messages:
                error_data = StreamResponse(
                    type="error",
                    content="No user message found",
                    done=True
                )
                yield f"data: {json.dumps(error_data.dict())}\n\n"
                return

            last_user_message = user_messages[-1]

            # Store user message in Firebase
            user_message_entity = await message_service.create_user_message(
                session_id=session.id,
                user_id=session.user_id,
                content=last_user_message.content,
            )

            logger.info(
                "user_message_stored_stream",
                session_id=session.id,
                message_id=user_message_entity.id,
            )

            # Start streaming response
            start_time = time.time()
            full_content = ""
            
            # Get streaming response from Agno
            async for token in agent.get_stream_response(
                chat_request.messages, session.id, user_id=session.user_id
            ):
                full_content += token
                
                # Send token to client
                stream_data = StreamResponse(
                    type="token",
                    content=token,
                    done=False
                )
                yield f"data: {json.dumps(stream_data.dict())}\n\n"

            processing_time = time.time() - start_time

            # Store complete assistant message in Firebase
            tokens_used = len(full_content.split()) * 1.3  # Rough estimate
            
            assistant_message_entity = await message_service.create_assistant_message(
                session_id=session.id,
                user_id=session.user_id,
                content=full_content,
                model_used=settings.LLM_MODEL,
                tokens_used=int(tokens_used),
                processing_time=processing_time,
                confidence_score=0.9,  # Default confidence
            )

            logger.info(
                "assistant_message_stored_stream",
                session_id=session.id,
                message_id=assistant_message_entity.id,
                tokens_used=int(tokens_used),
            )

            # Send completion signal
            completion_data = StreamResponse(
                type="done",
                content="",
                done=True
            )
            yield f"data: {json.dumps(completion_data.dict())}\n\n"

            logger.info(
                "chat_stream_completed",
                session_id=session.id,
                user_message_id=user_message_entity.id,
                assistant_message_id=assistant_message_entity.id,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(
                "chat_stream_failed",
                session_id=session.id,
                error=str(e),
                exc_info=True,
            )
            # Send error to client
            error_data = StreamResponse(
                type="error",
                content=f"Stream error: {str(e)}",
                done=True
            )
            yield f"data: {json.dumps(error_data.dict())}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type=CONTENT_TYPE_SSE,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.get("/messages", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
    limit: int = 50,
    order_by: str = "timestamp",
    direction: str = "asc",
    session: Session = Depends(get_current_session),
    message_service: MessageServiceDep = None,
):
    """Get all messages for a session using domain service.

    Args:
        request: The FastAPI request object for rate limiting.
        limit: Maximum number of messages to return.
        order_by: Field to order messages by.
        direction: Sort direction ('asc' or 'desc').
        session: The current session from the auth token.
        message_service: Message domain service for business logic.

    Returns:
        ChatResponse: All messages in the session.

    Raises:
        HTTPException: If there's an error retrieving the messages.
    """
    try:
        logger.info(
            "get_messages_request",
            session_id=session.id,
            limit=limit,
            order_by=order_by,
            direction=direction,
        )

        # Get messages from Firebase using the message service
        message_entities = await message_service.get_session_messages(
            session_id=session.id,
            user_id=session.user_id,
            limit=limit,
            order_by=order_by,
            direction=direction,
        )

        # Convert MessageEntity objects to the Message schema format
        messages = []
        for entity in message_entities:
            message_dict = {
                "role": entity.role,
                "content": entity.content,
            }
            messages.append(message_dict)

        logger.info(
            "get_messages_success",
            session_id=session.id,
            message_count=len(messages),
        )

        return ChatResponse(messages=messages)
    except Exception as e:
        logger.error(
            "get_messages_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
    session: Session = Depends(get_current_session),
    message_service: MessageServiceDep = None,
):
    """Clear all messages for a session using domain service.

    Args:
        request: The FastAPI request object for rate limiting.
        session: The current session from the auth token.
        message_service: Message domain service for business logic.

    Returns:
        dict: A message indicating the chat history was cleared.
    """
    try:
        logger.info(
            "clear_chat_history_request",
            session_id=session.id,
        )

        # Clear from agent's memory first
        await agent.clear_chat_history(session.id)
        
        # Clear messages from Firebase using the message service
        messages_cleared = await message_service.clear_session_messages(
            session_id=session.id,
            user_id=session.user_id,
        )
        
        logger.info(
            "chat_history_cleared",
            session_id=session.id,
            messages_cleared=messages_cleared,
        )

        return {
            "message": "Chat history cleared successfully",
            "messages_cleared": messages_cleared,
            "session_id": session.id,
        }
    except Exception as e:
        logger.error(
            "clear_chat_history_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history", response_model=ChatHistoryResponse)
@limiter.limit("30/minute")
async def get_chat_history(
    request: Request,
    history_request: ChatHistoryRequest,
    session: Session = Depends(get_current_session),
):
    """Get paginated chat history with advanced filtering.

    Args:
        request: FastAPI request object for rate limiting
        history_request: History request parameters
        session: Current session

    Returns:
        ChatHistoryResponse: Paginated chat history
    """
    try:
        # TODO: In a real implementation, this would
        # query the database with the provided filters
        logger.info(
            "chat_history_requested",
            session_id=session.id,
            limit=history_request.limit,
            offset=history_request.offset,
        )

        # TODO: Implement actual message store query
        import uuid
        from datetime import datetime

        messages = []
        total_count = 50  # TODO: Implement actual count from database

        # TODO: Generate actual messages from database
        for i in range(min(history_request.limit, 10)):
            messages.append(
                {
                    "id": str(uuid.uuid4()),
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Sample message {i + history_request.offset}",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "tokens": 10,
                    "processing_time": 0.5 if i % 2 == 1 else None,
                    "model_used": "agno-1.0" if i % 2 == 1 else None,
                    "context_documents": [],
                    "confidence_score": 0.9 if i % 2 == 1 else None,
                }
            )

        return ChatHistoryResponse(
            messages=messages,
            total_count=total_count,
            has_more=(history_request.offset + history_request.limit) < total_count,
            session_info={
                "session_id": session.id,
                "session_name": getattr(session, "name", "Chat Session"),
                "created_at": datetime.now().isoformat(),
                "message_count": total_count,
            },
        )

    except Exception as e:
        logger.error(
            "chat_history_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[ChatSearchResult])
@limiter.limit("20/minute")
async def search_chat_history(
    request: Request,
    search_request: ChatSearchRequest,
    session: Session = Depends(get_current_session),
):
    """Search through chat history with contextual relevance.

    Args:
        request: FastAPI request object for rate limiting
        search_request: Search parameters
        session: Current session

    Returns:
        List[ChatSearchResult]: Search results with relevance scores
    """
    try:
        logger.info(
            "chat_search_requested",
            session_id=session.id,
            query=search_request.query,
            limit=search_request.limit,
        )

        # TODO: Implement actual search using Elasticsearch or similar
        import uuid
        from datetime import datetime

        results = []
        for i in range(min(search_request.limit, 5)):
            message = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": f"This is a relevant response containing '{search_request.query}' in the context.",
                "timestamp": datetime.now().isoformat(),
                "session_id": session.id,
                "user_id": session.user_id,
                "tokens": 25,
                "processing_time": 1.2,
                "model_used": "agno-1.0",
                "context_documents": [str(uuid.uuid4())],
                "confidence_score": 0.85,
            }

            results.append(
                ChatSearchResult(
                    message=message,
                    relevance_score=0.9 - (i * 0.1),
                    context_snippet=f"...containing '{search_request.query}' in the context...",
                    session_name=getattr(session, "name", "Chat Session"),
                )
            )

        return results

    except Exception as e:
        logger.error(
            "chat_search_failed",
            session_id=session.id,
            query=search_request.query,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=ChatMetrics)
@limiter.limit("10/minute")
async def get_chat_metrics(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """Get comprehensive chat metrics and analytics.

    Args:
        request: FastAPI request object for rate limiting
        session: Current session

    Returns:
        ChatMetrics: Chat analytics and metrics
    """
    try:
        logger.info("chat_metrics_requested", session_id=session.id)

        # TODO: Implement actual metrics aggregation from database
        metrics = ChatMetrics(
            total_messages=1250,
            total_sessions=75,
            avg_messages_per_session=16.7,
            avg_response_time=1.8,
            most_active_users=[
                {"user_id": session.user_id, "message_count": 45},
                {"user_id": 2, "message_count": 38},
                {"user_id": 3, "message_count": 32},
            ],
            popular_topics=[
                {"topic": "documentos legislativos", "count": 125},
                {"topic": "pesquisa jurídica", "count": 89},
                {"topic": "análise de contratos", "count": 67},
            ],
            model_usage={"agno-1.0": 85.2, "agno-0.9": 14.8},
            daily_stats=[
                {"date": "2025-01-20", "messages": 45, "sessions": 8},
                {"date": "2025-01-21", "messages": 52, "sessions": 9},
                {"date": "2025-01-22", "messages": 38, "sessions": 6},
            ],
            token_usage={
                "total_tokens": 125000,
                "avg_tokens_per_message": 28.5,
                "cost_estimate_usd": 12.50,
            },
        )

        return metrics

    except Exception as e:
        logger.error(
            "chat_metrics_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ChatExportResponse)
@limiter.limit("5/minute")
async def export_chat_data(
    request: Request,
    export_request: ChatExportRequest,
    session: Session = Depends(get_current_session),
):
    """Export chat data in various formats.

    Args:
        request: FastAPI request object for rate limiting
        export_request: Export parameters
        session: Current session

    Returns:
        ChatExportResponse: Export file information
    """
    try:
        logger.info(
            "chat_export_requested",
            session_id=session.id,
            format=export_request.format,
            user_id=export_request.user_id,
        )

        # TODO: Implement actual file generation
        import uuid
        from datetime import (
            datetime,
            timedelta,
        )

        # Simulate file generation
        file_id = str(uuid.uuid4())
        file_url = f"/api/v1/chatbot/downloads/{file_id}.{export_request.format}"
        message_count = 150

        return ChatExportResponse(
            success=True,
            file_url=file_url,
            file_size=25600,  # 25KB
            message_count=message_count,
            export_format=export_request.format,
            expires_at=datetime.now() + timedelta(hours=24),  # 24h expiry
        )

    except Exception as e:
        logger.error(
            "chat_export_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", response_model=ChatInsightsResponse)
@limiter.limit("5/minute")
async def get_chat_insights(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """Get AI-generated insights about chat patterns and usage.

    Args:
        request: FastAPI request object for rate limiting
        session: Current session

    Returns:
        ChatInsightsResponse: AI-generated insights and recommendations
    """
    try:
        logger.info("chat_insights_requested", session_id=session.id)

        # TODO: Implement AI-powered pattern analysis
        from datetime import datetime

        insights = [
            {
                "insight_type": "usage_pattern",
                "title": "Peak Usage Hours",
                "description": "Most chat activity occurs between 9-11 AM and 2-4 PM",
                "confidence": 0.92,
                "data": {"peak_hours": [9, 10, 14, 15], "activity_score": 85},
                "generated_at": datetime.now().isoformat(),
            },
            {
                "insight_type": "topic_trend",
                "title": "Growing Interest in Contract Analysis",
                "description": "Questions about contract analysis have increased 35% this month",
                "confidence": 0.87,
                "data": {"growth_rate": 0.35, "topic": "contract_analysis"},
                "generated_at": datetime.now().isoformat(),
            },
            {
                "insight_type": "user_behavior",
                "title": "Users Prefer Shorter Responses",
                "description": "Messages under 200 words receive 45% higher satisfaction ratings",
                "confidence": 0.79,
                "data": {"optimal_length": 150, "satisfaction_boost": 0.45},
                "generated_at": datetime.now().isoformat(),
            },
        ]

        return ChatInsightsResponse(
            insights=insights,
            summary="Overall chat engagement is high with users actively seeking legal document assistance. Peak usage aligns with business hours, and there's growing demand for contract analysis features.",
            recommendations=[
                "Consider adding more contract analysis templates",
                "Optimize response length to 150-200 words for better engagement",
                "Schedule system maintenance outside peak hours (9-11 AM, 2-4 PM)",
                "Develop specialized workflows for legal document processing",
            ],
            generated_at=datetime.now(),
        )

    except Exception as e:
        logger.error(
            "chat_insights_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
