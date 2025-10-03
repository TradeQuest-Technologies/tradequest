"""
Email service for sending notifications and reports
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
import structlog
from jinja2 import Template
from app.core.config import settings

logger = structlog.get_logger()

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send an email"""
        
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, using mock email service")
                return await self._send_mock_email(to_email, subject, html_content)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", to_email=to_email, error=str(e))
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email"""
        
        try:
            filename = attachment.get("filename")
            content = attachment.get("content")
            content_type = attachment.get("content_type", "application/octet-stream")
            
            if filename and content:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error("Failed to add attachment", error=str(e))
    
    async def _send_mock_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Mock email service for development"""
        
        logger.info("Mock email sent", to_email=to_email, subject=subject)
        return True
    
    async def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification email"""
        
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/verify?token={verification_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Verify Your Email Address</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Thank you for signing up for TradeQuest! Please click the button below to verify your email address.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: #005F73; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{verification_url}" style="color: #005F73;">{verification_url}</a>
                </p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This link will expire in 24 hours. If you didn't create an account with TradeQuest, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address
        
        Thank you for signing up for TradeQuest! Please visit the following link to verify your email address:
        
        {verification_url}
        
        This link will expire in 24 hours. If you didn't create an account with TradeQuest, you can safely ignore this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Verify Your TradeQuest Email Address",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_magic_link_email(self, to_email: str, magic_link_url: str) -> bool:
        """Send magic link email for passwordless login"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Your Magic Link</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Click the button below to sign in to your TradeQuest account. No password required!
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{magic_link_url}" 
                       style="background: #005F73; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Sign In to TradeQuest
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{magic_link_url}" style="color: #005F73;">{magic_link_url}</a>
                </p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This link will expire in 15 minutes. If you didn't request this sign-in link, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Your Magic Link
        
        Click the link below to sign in to your TradeQuest account. No password required!
        
        {magic_link_url}
        
        This link will expire in 15 minutes. If you didn't request this sign-in link, you can safely ignore this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Your TradeQuest Magic Link",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_2fa_code_email(self, to_email: str, code: str) -> bool:
        """Send a one-time verification code for email-based 2FA"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Your Verification Code</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Use the following code to complete your sign-in:
                </p>
                <div style="text-align: center; margin: 24px 0;">
                    <div style="display: inline-block; font-size: 32px; letter-spacing: 6px; font-weight: 700; background: #fff; border: 1px solid #e5e7eb; padding: 12px 18px; border-radius: 10px; color: #111827;">
                        {code}
                    </div>
                </div>
                <p style="color: #666; font-size: 14px;">
                    This code expires in 10 minutes. If you didn't request this, you can ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        text_content = f"Your TradeQuest verification code is: {code}. It expires in 10 minutes."
        return await self.send_email(
            to_email=to_email,
            subject="Your TradeQuest Verification Code",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    You requested to reset your password for your TradeQuest account. Click the button below to create a new password.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #005F73; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{reset_url}" style="color: #005F73;">{reset_url}</a>
                </p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password
        
        You requested to reset your password for your TradeQuest account. Please visit the following link to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Reset Your TradeQuest Password",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_account_deletion_confirmation(self, email: str, deletion_date: str) -> bool:
        """Send account deletion confirmation email"""
        
        try:
            subject = "TradeQuest Account Deletion Confirmation"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Account Deletion Confirmation</h2>
                    
                    <p>Your TradeQuest account deletion has been requested and will be processed on:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Deletion Date:</strong> {deletion_date}
                    </div>
                    
                    <p>During this grace period, you can:</p>
                    <ul>
                        <li>Cancel the deletion request</li>
                        <li>Export your data</li>
                        <li>Contact support if you have questions</li>
                    </ul>
                    
                    <p>If you did not request this deletion, please contact our support team immediately.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #666;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Account Deletion Confirmation
            
            Your TradeQuest account deletion has been requested and will be processed on: {deletion_date}
            
            During this grace period, you can:
            - Cancel the deletion request
            - Export your data
            - Contact support if you have questions
            
            If you did not request this deletion, please contact our support team immediately.
            
            This is an automated message. Please do not reply to this email.
            """
            
            await self.send_email(email, subject, text_content, html_content)
            
            logger.info("Account deletion confirmation sent", email=email, deletion_date=deletion_date)
            return True
            
        except Exception as e:
            logger.error("Failed to send account deletion confirmation", error=str(e))
            return False
    
    async def send_weekly_report_email(self, to_email: str, report_data: Dict[str, Any], pdf_content: Optional[bytes] = None) -> bool:
        """Send weekly report email"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Your Weekly Trading Report</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Here's your weekly trading performance summary for {report_data.get('week_start', 'this week')}.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Key Metrics</h3>
                    <ul style="color: #666; list-style: none; padding: 0;">
                        <li style="margin: 10px 0;"><strong>Total Trades:</strong> {report_data.get('total_trades', 0)}</li>
                        <li style="margin: 10px 0;"><strong>Win Rate:</strong> {report_data.get('win_rate', 0):.1%}</li>
                        <li style="margin: 10px 0;"><strong>Total P&L:</strong> ${report_data.get('total_pnl', 0):.2f}</li>
                        <li style="margin: 10px 0;"><strong>Consistency Score:</strong> {report_data.get('consistency_score', 0):.1%}</li>
                    </ul>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Action Items</h3>
                    <ul style="color: #666;">
                        {''.join([f'<li style="margin: 5px 0;">{item}</li>' for item in report_data.get('action_items', [])])}
                    </ul>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Keep up the great work! Continue focusing on your trading plan and risk management.
                </p>
            </div>
        </body>
        </html>
        """
        
        attachments = []
        if pdf_content:
            attachments.append({
                "filename": f"weekly_report_{report_data.get('week_start', 'week')}.pdf",
                "content": pdf_content,
                "content_type": "application/pdf"
            })
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Weekly Trading Report - {report_data.get('week_start', 'This Week')}",
            html_content=html_content,
            attachments=attachments
        )
    
    async def send_alert_email(self, to_email: str, alert_data: Dict[str, Any]) -> bool:
        """Send trading alert email"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest Alert</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Trading Alert Triggered</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    {alert_data.get('message', 'A trading alert has been triggered.')}
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Alert Details</h3>
                    <ul style="color: #666; list-style: none; padding: 0;">
                        <li style="margin: 10px 0;"><strong>Rule:</strong> {alert_data.get('rule_name', 'Unknown')}</li>
                        <li style="margin: 10px 0;"><strong>Triggered:</strong> {alert_data.get('triggered_at', 'Unknown time')}</li>
                        <li style="margin: 10px 0;"><strong>Status:</strong> {alert_data.get('status', 'Active')}</li>
                    </ul>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Please review your trading plan and consider your risk management rules.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"TradeQuest Alert: {alert_data.get('rule_name', 'Trading Alert')}",
            html_content=html_content
        )
