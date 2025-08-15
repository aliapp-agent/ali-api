"""WhatsApp client mock implementation."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Mock WhatsApp client for testing purposes."""
    
    def __init__(self):
        """Initialize WhatsApp client."""
        self.connected = False
        logger.info("WhatsApp client initialized (mock)")
    
    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send message via WhatsApp.
        
        Args:
            phone_number: Target phone number
            message: Message content
            
        Returns:
            Dict with send result
        """
        logger.info(f"Mock sending WhatsApp message to {phone_number}: {message[:50]}...")
        return {
            "success": True,
            "message_id": "mock_message_123",
            "phone_number": phone_number
        }
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get message delivery status.
        
        Args:
            message_id: Message ID to check
            
        Returns:
            Dict with status info
        """
        return {
            "message_id": message_id,
            "status": "delivered",
            "timestamp": "2025-01-29T10:00:00Z"
        }
    
    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            Connection status
        """
        return True  # Mock always connected
    
    async def connect(self) -> bool:
        """Connect to WhatsApp service.
        
        Returns:
            Connection success status
        """
        self.connected = True
        logger.info("WhatsApp client connected (mock)")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from WhatsApp service."""
        self.connected = False
        logger.info("WhatsApp client disconnected (mock)")