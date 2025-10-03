import asyncio
import aiohttp
from typing import Optional
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class SMSService:
    """Service for sending SMS notifications"""
    
    def __init__(self):
        # Using Twilio as the SMS provider
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
    
    async def send_sms(
        self, 
        phone_number: str, 
        message: str
    ) -> bool:
        """Send SMS message"""
        
        try:
            # Format phone number (ensure it starts with +)
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
            # Prepare request data
            data = {
                'From': self.from_number,
                'To': phone_number,
                'Body': message
            }
            
            # Send SMS via Twilio API
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(
                    f"{self.base_url}/Messages.json",
                    data=data,
                    auth=auth
                ) as response:
                    
                    if response.status == 201:
                        result = await response.json()
                        logger.info("SMS sent successfully", 
                                  message_sid=result.get('sid'),
                                  to=phone_number)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("SMS sending failed", 
                                   status=response.status,
                                   error=error_text,
                                   to=phone_number)
                        return False
        
        except Exception as e:
            logger.error("SMS service error", error=str(e), to=phone_number)
            return False
    
    async def send_bulk_sms(
        self, 
        phone_numbers: list[str], 
        message: str
    ) -> dict:
        """Send SMS to multiple recipients"""
        
        results = {
            "total": len(phone_numbers),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Send SMS to each number
        tasks = [
            self.send_sms(phone_number, message) 
            for phone_number in phone_numbers
        ]
        
        sms_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(sms_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append({
                    "phone_number": phone_numbers[i],
                    "error": str(result)
                })
            elif result:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Check if it starts with + and has 10-15 digits
        if cleaned.startswith('+') and len(cleaned) >= 11 and len(cleaned) <= 16:
            return True
        
        return False
    
    async def get_sms_status(self, message_sid: str) -> Optional[dict]:
        """Get SMS delivery status"""
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.get(
                    f"{self.base_url}/Messages/{message_sid}.json",
                    auth=auth
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error("Failed to get SMS status", 
                                   message_sid=message_sid,
                                   status=response.status)
                        return None
        
        except Exception as e:
            logger.error("SMS status check error", 
                        message_sid=message_sid,
                        error=str(e))
            return None