import requests
from agno.tools.function import Function

from app.core.config import settings
from app.core.logging import logger


def send_text_message_via_whatsapp(
    formated_phone_number: str, message_content: str
) -> bool:
    """
    Send a text message via WhatsApp.

    Args:
        formated_phone_number (str): The phone number in the correct format.
        message_content (str): The content of the message.

    Returns:
        bool: a boolean indicating whether the message was sent successfully.
    """
    try:
        url = settings.EVOLUTION_API_URL + \
            "/message/sendText/" + settings.EVOLUTION_INSTANCE

        payload = {
            "number": formated_phone_number,
            "text": message_content,
            "delay": 1000,
        }
        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if response.status_code != 201:
            logger.error(f"WhatsApp message failed: {response.status_code} - {response.text}")
            return False

        logger.info(f"WhatsApp message sent successfully to {formated_phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False


whatsapp_tool = Function(
    function=send_text_message_via_whatsapp,
    name="send_whatsapp_message",
    description="Send a text message via WhatsApp using Evolution API",
)