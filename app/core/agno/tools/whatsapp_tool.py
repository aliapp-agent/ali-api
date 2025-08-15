"""WhatsApp tool for sending messages via Evolution API."""

import requests
from agno.tools.function import Function

from app.core.config import settings
from app.core.logging import logger


def send_text_message_via_whatsapp(
    formated_phone_number: str, message_content: str
) -> str:
    """Send a text message via WhatsApp using Evolution API.

    Args:
        formated_phone_number (str): The phone number in the correct format (e.g., "5511999999999").
        message_content (str): The content of the message to send.

    Returns:
        str: Status message indicating success or failure.
    """
    try:
        # Validate inputs
        if not formated_phone_number or not message_content:
            error_msg = "Phone number and message content are required"
            logger.error("whatsapp_tool_validation_error", error=error_msg)
            return f"Error: {error_msg}"

        if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_INSTANCE or not settings.EVOLUTION_API_KEY:
            error_msg = "Evolution API configuration incomplete. Check EVOLUTION_API_URL, EVOLUTION_INSTANCE, and EVOLUTION_API_KEY"
            logger.error("whatsapp_tool_config_error", error=error_msg)
            return f"Error: {error_msg}"

        # Build URL
        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}"

        payload = {
            "number": formated_phone_number,
            "text": message_content,
            "delay": 1000,
        }

        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }

        logger.info(
            "sending_whatsapp_message",
            phone_number=formated_phone_number,
            message_length=len(message_content),
            url=url
        )

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        success_status = 201
        if response.status_code == success_status:
            success_msg = f"WhatsApp message sent successfully to {formated_phone_number}"
            logger.info(
                "whatsapp_message_sent_successfully",
                phone_number=formated_phone_number,
                response_status=response.status_code
            )
            return success_msg
        else:
            error_msg = f"WhatsApp message failed: {response.status_code} - {response.text}"
            logger.error(
                "whatsapp_message_send_failed",
                phone_number=formated_phone_number,
                status_code=response.status_code,
                response_text=response.text
            )
            return f"Error: {error_msg}"

    except requests.exceptions.Timeout:
        error_msg = "Request timeout when sending WhatsApp message"
        logger.error("whatsapp_tool_timeout", phone_number=formated_phone_number, error=error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error when sending WhatsApp message. Check Evolution API URL"
        logger.error("whatsapp_tool_connection_error", phone_number=formated_phone_number, error=error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error sending WhatsApp message: {str(e)}"
        logger.error(
            "whatsapp_tool_unexpected_error",
            phone_number=formated_phone_number,
            error=str(e),
            exc_info=True
        )
        return f"Error: {error_msg}"


# Create the WhatsApp tool
try:
    whatsapp_tool = Function(
        function=send_text_message_via_whatsapp,
        name="send_whatsapp_message",
        description="Send a text message via WhatsApp using Evolution API. Requires a formatted phone number (e.g., '5511999999999') and message content.",
    )
    logger.info("whatsapp_tool_created_successfully")
except Exception as e:
    logger.error("failed_to_create_whatsapp_tool", error=str(e), exc_info=True)
    # DO NOT create dummy tool - this should fail AgnoAgent initialization
    raise Exception(f"Critical error creating WhatsApp tool: {str(e)}") from e
