"""
Telegram bot service for sending alerts and notifications
"""

import aiohttp
import os
from typing import Dict, Any, Optional, List
import structlog
import json

logger = structlog.get_logger()

class TelegramService:
    """Service for sending Telegram messages"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
    
    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a message to a Telegram chat"""
        
        try:
            if not self.bot_token or not self.base_url:
                logger.warning("Telegram bot token not configured, using mock service")
                return await self._send_mock_message(chat_id, message)
            
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Telegram message sent successfully", chat_id=chat_id)
                            return True
                        else:
                            logger.error("Telegram API error", error=result.get("description"))
                            return False
                    else:
                        logger.error("Telegram API HTTP error", status=response.status)
                        return False
                        
        except Exception as e:
            logger.error("Failed to send Telegram message", chat_id=chat_id, error=str(e))
            return False
    
    async def _send_mock_message(self, chat_id: str, message: str) -> bool:
        """Mock Telegram service for development"""
        
        logger.info("Mock Telegram message sent", chat_id=chat_id, message=message[:100])
        return True
    
    async def send_alert_message(self, chat_id: str, alert_data: Dict[str, Any]) -> bool:
        """Send trading alert message"""
        
        message = f"""
🚨 <b>Trading Alert Triggered</b>

<b>Rule:</b> {alert_data.get('rule_name', 'Unknown')}
<b>Time:</b> {alert_data.get('triggered_at', 'Unknown')}
<b>Status:</b> {alert_data.get('status', 'Active')}

<b>Details:</b>
{alert_data.get('message', 'A trading alert has been triggered.')}

Please review your trading plan and consider your risk management rules.
        """.strip()
        
        return await self.send_message(chat_id, message)
    
    async def send_daily_summary(self, chat_id: str, summary_data: Dict[str, Any]) -> bool:
        """Send daily trading summary"""
        
        message = f"""
📊 <b>Daily Trading Summary</b>

<b>Date:</b> {summary_data.get('date', 'Today')}
<b>Trades:</b> {summary_data.get('trades_count', 0)}
<b>P&L:</b> ${summary_data.get('total_pnl', 0):.2f}
<b>Win Rate:</b> {summary_data.get('win_rate', 0):.1%}

<b>AI Note:</b>
{summary_data.get('ai_note', 'No analysis available.')}

Keep up the great work! 🚀
        """.strip()
        
        return await self.send_message(chat_id, message)
    
    async def send_weekly_report(self, chat_id: str, report_data: Dict[str, Any]) -> bool:
        """Send weekly trading report"""
        
        message = f"""
📈 <b>Weekly Trading Report</b>

<b>Week:</b> {report_data.get('week_start', 'This Week')}
<b>Total Trades:</b> {report_data.get('total_trades', 0)}
<b>Win Rate:</b> {report_data.get('win_rate', 0):.1%}
<b>Total P&L:</b> ${report_data.get('total_pnl', 0):.2f}
<b>Consistency Score:</b> {report_data.get('consistency_score', 0):.1%}

<b>Action Items:</b>
{chr(10).join([f"• {item}" for item in report_data.get('action_items', [])])}

Continue focusing on your trading plan! 💪
        """.strip()
        
        return await self.send_message(chat_id, message)
    
    async def send_test_message(self, chat_id: str) -> bool:
        """Send test message to verify bot connection"""
        
        message = """
🤖 <b>TradeQuest Bot Test</b>

This is a test message from your TradeQuest bot. If you're receiving this, your Telegram integration is working correctly!

You'll receive trading alerts, daily summaries, and weekly reports here.
        """.strip()
        
        return await self.send_message(chat_id, message)
    
    async def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Get bot information"""
        
        try:
            if not self.bot_token or not self.base_url:
                return None
            
            url = f"{self.base_url}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return result.get("result")
                        else:
                            logger.error("Telegram bot info error", error=result.get("description"))
                            return None
                    else:
                        logger.error("Telegram bot info HTTP error", status=response.status)
                        return None
                        
        except Exception as e:
            logger.error("Failed to get bot info", error=str(e))
            return None
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook for receiving updates"""
        
        try:
            if not self.bot_token or not self.base_url:
                logger.warning("Telegram bot token not configured")
                return False
            
            url = f"{self.base_url}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Telegram webhook set successfully", webhook_url=webhook_url)
                            return True
                        else:
                            logger.error("Telegram webhook error", error=result.get("description"))
                            return False
                    else:
                        logger.error("Telegram webhook HTTP error", status=response.status)
                        return False
                        
        except Exception as e:
            logger.error("Failed to set Telegram webhook", error=str(e))
            return False
    
    async def delete_webhook(self) -> bool:
        """Delete webhook"""
        
        try:
            if not self.bot_token or not self.base_url:
                return False
            
            url = f"{self.base_url}/deleteWebhook"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Telegram webhook deleted successfully")
                            return True
                        else:
                            logger.error("Telegram webhook delete error", error=result.get("description"))
                            return False
                    else:
                        logger.error("Telegram webhook delete HTTP error", status=response.status)
                        return False
                        
        except Exception as e:
            logger.error("Failed to delete Telegram webhook", error=str(e))
            return False
