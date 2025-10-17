"""
Encryption service for securely storing API keys and secrets
"""

from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import hashlib
import structlog

logger = structlog.get_logger()

class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        # Generate encryption key from JWT secret (or use dedicated encryption key)
        # In production, use AWS KMS or dedicated encryption key
        key_material = settings.JWT_SECRET.encode()
        # Derive a proper Fernet key (32 bytes base64-encoded)
        derived_key = hashlib.sha256(key_material).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(derived_key))
    
    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted bytes
        """
        try:
            return self.cipher.encrypt(plaintext.encode())
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise
    
    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt bytes to string
        
        Args:
            ciphertext: Encrypted bytes
            
        Returns:
            Decrypted string
        """
        try:
            return self.cipher.decrypt(ciphertext).decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise
    
    def mask_api_key(self, api_key: str, show_chars: int = 4) -> str:
        """
        Mask an API key for display
        
        Args:
            api_key: API key to mask
            show_chars: Number of characters to show at the end
            
        Returns:
            Masked string like "****abc123"
        """
        if not api_key or len(api_key) <= show_chars:
            return "****"
        
        return "****" + api_key[-show_chars:]

# Global encryption service instance
encryption_service = EncryptionService()

