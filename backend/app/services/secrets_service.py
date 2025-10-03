"""
AWS Secrets Manager service for secure configuration management
"""

import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class SecretsService:
    """Service for managing secrets via AWS Secrets Manager"""
    
    def __init__(self):
        self.secret_name = settings.SECRETS_MANAGER_SECRET_NAME
        self._secrets_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        if self.secret_name:
            self._init_secrets_client()
        else:
            logger.warning("No secrets manager secret name configured")
    
    def _init_secrets_client(self):
        """Initialize AWS Secrets Manager client"""
        try:
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                # Use explicit credentials
                self.secrets_client = boto3.client(
                    'secretsmanager',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
            else:
                # Use IAM role or environment credentials
                self.secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
            
            logger.info(f"Secrets Manager initialized with secret: {self.secret_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found for Secrets Manager")
            raise
        except Exception as e:
            logger.error(f"Secrets Manager initialization failed: {e}")
            raise
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value by key
        
        Args:
            key: Secret key to retrieve
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        if not self.secret_name:
            return default
        
        try:
            # Check cache first
            if key in self._secrets_cache:
                return self._secrets_cache[key]
            
            # Fetch from AWS Secrets Manager
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            
            # Parse the secret
            secret_data = json.loads(response['SecretString'])
            
            # Cache the secrets
            self._secrets_cache.update(secret_data)
            
            value = secret_data.get(key, default)
            logger.debug(f"Retrieved secret: {key}")
            return value
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret {self.secret_name} not found")
            else:
                logger.error(f"Failed to retrieve secret {key}: {e}")
            return default
        except json.JSONDecodeError:
            logger.error(f"Failed to parse secret JSON for {self.secret_name}")
            return default
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {key}: {e}")
            return default
    
    def get_all_secrets(self) -> Dict[str, Any]:
        """
        Get all secrets from the secret
        
        Returns:
            Dictionary of all secrets
        """
        if not self.secret_name:
            return {}
        
        try:
            # Check cache first
            if self._secrets_cache:
                return self._secrets_cache.copy()
            
            # Fetch from AWS Secrets Manager
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            
            # Parse the secret
            secret_data = json.loads(response['SecretString'])
            
            # Cache the secrets
            self._secrets_cache.update(secret_data)
            
            logger.debug(f"Retrieved all secrets from {self.secret_name}")
            return secret_data.copy()
            
        except ClientError as e:
            logger.error(f"Failed to retrieve secrets: {e}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse secret JSON for {self.secret_name}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error retrieving secrets: {e}")
            return {}
    
    def update_secret(self, key: str, value: str) -> bool:
        """
        Update a secret value
        
        Args:
            key: Secret key to update
            value: New secret value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.secret_name:
            logger.warning("No secrets manager configured for updates")
            return False
        
        try:
            # Get current secrets
            current_secrets = self.get_all_secrets()
            
            # Update the specific key
            current_secrets[key] = value
            
            # Update the secret in AWS
            self.secrets_client.update_secret(
                SecretId=self.secret_name,
                SecretString=json.dumps(current_secrets)
            )
            
            # Update cache
            self._secrets_cache[key] = value
            
            logger.info(f"Updated secret: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update secret {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating secret {key}: {e}")
            return False
    
    def clear_cache(self):
        """Clear the secrets cache"""
        self._secrets_cache.clear()
        logger.debug("Secrets cache cleared")


# Global secrets service instance
secrets_service = SecretsService()


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value, checking secrets manager first, then environment
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    # First try secrets manager
    secret_value = secrets_service.get_secret(key)
    if secret_value is not None:
        return secret_value
    
    # Fallback to environment variable
    import os
    return os.getenv(key, default)
