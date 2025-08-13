"""WhatsApp webhook endpoints for Evolution API integration.

This module handles incoming webhooks from Evolution API, processes WhatsApp messages,
and sends responses using the AgnoAgent chatbot.
"""

import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


async def get_agno_agent(request: Request):
    """Get the AgnoAgent instance from app state."""
    agno_agent = getattr(request.app.state, 'agno_agent', None)
    if not agno_agent:
        logger.error("agno_agent_not_available")
        raise HTTPException(
            status_code=503,
            detail="AI agent not available"
        )
    return agno_agent


def extract_phone_number(remote_jid: str) -> str:
    """Extract phone number from WhatsApp JID format.

    Args:
        remote_jid: WhatsApp JID (e.g., "5511999999999@s.whatsapp.net")

    Returns:
        Phone number without WhatsApp domain
    """
    return remote_jid.split('@')[0] if '@' in remote_jid else remote_jid


def format_phone_number(phone: str) -> str:
    """Format phone number for WhatsApp API.

    Args:
        phone: Phone number

    Returns:
        Formatted phone number
    """
    # Remove any non-digit characters
    clean_phone = ''.join(filter(str.isdigit, phone))

    # Ensure it starts with country code (assumes Brazil +55 if not provided)
    if not clean_phone.startswith('55') and len(clean_phone) == 11:
        clean_phone = '55' + clean_phone
    elif not clean_phone.startswith('55') and len(clean_phone) == 10:
        clean_phone = '55' + clean_phone

    return clean_phone


async def process_whatsapp_message(
    phone_number: str,
    message_text: str,
    message_id: str,
    agno_agent,
    background_tasks: BackgroundTasks
) -> None:
    """Process incoming WhatsApp message and send AI response.

    Args:
        phone_number: Sender's phone number
        message_text: Message content
        message_id: Message ID for tracking
        agno_agent: AgnoAgent instance
        background_tasks: FastAPI background tasks
    """
    try:
        logger.info(
            "processing_whatsapp_message",
            phone_number=phone_number,
            message_id=message_id,
            message_preview=message_text[:100] + "..." if len(message_text) > 100 else message_text
        )

        # Create a session ID based on phone number
        session_id = f"whatsapp_{phone_number}"

        # Process message with AgnoAgent
        response = await agno_agent.process_message(
            message=message_text,
            session_id=session_id,
            metadata={
                "source": "whatsapp",
                "phone_number": phone_number,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            }
        )

        if response and response.get('response'):
            # Format phone number for sending
            formatted_phone = format_phone_number(phone_number)

            logger.info(
                "sending_whatsapp_response",
                phone_number=formatted_phone,
                response_preview=response['response'][:100] + "..." if len(response['response']) > 100 else response['response']
            )

            # The whatsapp_tool will be called by AgnoAgent if needed
            # We don't need to manually send the message here as the agent
            # will use the available tools including whatsapp_tool

        logger.info(
            "whatsapp_message_processed_successfully",
            phone_number=phone_number,
            message_id=message_id,
            response_generated=bool(response)
        )

    except Exception as e:
        logger.error(
            "error_processing_whatsapp_message",
            phone_number=phone_number,
            message_id=message_id,
            error=str(e),
            traceback=traceback.format_exc()
        )


@router.post("/webhook/evolution")
async def evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    agno_agent=Depends(get_agno_agent)
):
    """Handle incoming webhooks from Evolution API.

    This endpoint receives various types of events from Evolution API,
    processes incoming messages, and responds using the AI agent.
    """
    try:
        # Get request body
        body = await request.body()

        if not body:
            logger.warning("evolution_webhook_empty_body")
            return JSONResponse(content={"status": "ok"}, status_code=200)

        # Parse JSON
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(
                "evolution_webhook_invalid_json",
                error=str(e),
                body_preview=body.decode('utf-8')[:200] + "..." if len(body) > 200 else body.decode('utf-8')
            )
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Log incoming webhook
        logger.info(
            "evolution_webhook_received",
            event_type=data.get('event'),
            instance=data.get('instance'),
            data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict"
        )

        # Handle different event types
        event = data.get('event')

        if event == 'messages.upsert':
            # Handle incoming messages
            await handle_message_upsert(data, agno_agent, background_tasks)

        elif event == 'connection.update':
            # Handle connection status updates
            logger.info(
                "whatsapp_connection_update",
                instance=data.get('instance'),
                connection_state=data.get('data', {}).get('state')
            )

        elif event == 'qrcode.updated':
            # Handle QR code updates
            logger.info(
                "whatsapp_qrcode_updated",
                instance=data.get('instance'),
                qr_available=bool(data.get('data', {}).get('qrcode'))
            )

        else:
            logger.debug(
                "evolution_webhook_unhandled_event",
                event=event,
                instance=data.get('instance')
            )

        return JSONResponse(content={"status": "ok"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "evolution_webhook_error",
            error=str(e),
            traceback=traceback.format_exc()
        )
        raise HTTPException(
            status_code=500,
            detail="Error processing webhook"
        )


async def handle_message_upsert(
    data: Dict[str, Any],
    agno_agent,
    background_tasks: BackgroundTasks
) -> None:
    """Handle incoming message events from Evolution API.

    Args:
        data: Webhook data from Evolution API
        agno_agent: AgnoAgent instance
        background_tasks: FastAPI background tasks
    """
    try:
        messages = data.get('data', {}).get('messages', [])

        for message_data in messages:
            # Skip messages sent by us (fromMe = True)
            if message_data.get('key', {}).get('fromMe', False):
                continue

            # Extract message information
            remote_jid = message_data.get('key', {}).get('remoteJid', '')
            message_id = message_data.get('key', {}).get('id', '')

            # Get message content
            message_info = message_data.get('message', {})

            # Handle different message types
            message_text = None

            if 'conversation' in message_info:
                # Text message
                message_text = message_info['conversation']
            elif 'extendedTextMessage' in message_info:
                # Extended text message
                message_text = message_info['extendedTextMessage'].get('text', '')
            else:
                # Other message types (media, etc.) - skip for now
                logger.debug(
                    "whatsapp_unsupported_message_type",
                    message_types=list(message_info.keys()),
                    remote_jid=remote_jid
                )
                continue

            if not message_text or not message_text.strip():
                continue

            # Extract phone number
            phone_number = extract_phone_number(remote_jid)

            # Process message in background
            background_tasks.add_task(
                process_whatsapp_message,
                phone_number=phone_number,
                message_text=message_text.strip(),
                message_id=message_id,
                agno_agent=agno_agent,
                background_tasks=background_tasks
            )

            logger.info(
                "whatsapp_message_queued_for_processing",
                phone_number=phone_number,
                message_id=message_id
            )

    except Exception as e:
        logger.error(
            "error_handling_message_upsert",
            error=str(e),
            traceback=traceback.format_exc()
        )


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook is working."""
    return JSONResponse(
        content={
            "status": "ok",
            "message": "WhatsApp webhook is working",
            "timestamp": datetime.now().isoformat(),
            "evolution_config": {
                "api_url": settings.EVOLUTION_API_URL,
                "instance": settings.EVOLUTION_INSTANCE,
                "api_key_configured": bool(settings.EVOLUTION_API_KEY)
            }
        },
        status_code=200
    )


@router.post("/webhook/test-message")
async def test_message_processing(
    request: Request,
    background_tasks: BackgroundTasks,
    agno_agent=Depends(get_agno_agent)
):
    """Test endpoint to simulate WhatsApp message processing.

    Request body:
    {
        "phone_number": "5511999999999",
        "message": "Hello, test message"
    }
    """
    try:
        data = await request.json()

        phone_number = data.get('phone_number')
        message = data.get('message')

        if not phone_number or not message:
            raise HTTPException(
                status_code=400,
                detail="phone_number and message are required"
            )

        # Process test message
        background_tasks.add_task(
            process_whatsapp_message,
            phone_number=phone_number,
            message_text=message,
            message_id=f"test_{datetime.now().timestamp()}",
            agno_agent=agno_agent,
            background_tasks=background_tasks
        )

        return JSONResponse(
            content={
                "status": "ok",
                "message": "Test message queued for processing",
                "phone_number": phone_number,
                "test_message": message
            },
            status_code=200
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "test_message_processing_error",
            error=str(e),
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Internal server error")
