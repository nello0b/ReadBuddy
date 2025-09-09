# backend/key_vault.py

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
import logging

logger = logging.getLogger(__name__)

# Azure Key Vault configuration (moved here to avoid circular import)
AZURE_KEY_VAULT_NAME = "readbuddykeyvault"
AZURE_KEY_VAULT_URI = f"https://{AZURE_KEY_VAULT_NAME}.vault.azure.net/"


class KeyVault:

    def __init__(self):
        """
        Initialize the KeyVault client with credentials.
        """
        try:
            from secret_credential import tenantId, clientId, clientSecret

            logger.info(
                f"Using service principal authentication with tenant: {tenantId}"
            )
            credential = ClientSecretCredential(
                tenant_id=tenantId, client_id=clientId, client_secret=clientSecret
            )
            print("✅ Successfully set up service principal credentials 🎉")
        except ImportError:
            logger.info(
                "Service principal credentials not found, using DefaultAzureCredential"
            )
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=False,
                additionally_allowed_tenants=["*"],
            )
            print("✅ Falling back to DefaultAzureCredential 🎉")
        except Exception as e:
            logger.error(f"Error setting up service principal credentials: {e}")
            logger.info("Falling back to DefaultAzureCredential")
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=False,
                additionally_allowed_tenants=["*"],
            )

        try:
            client = SecretClient(vault_url=AZURE_KEY_VAULT_URI, credential=credential)

            # Retrieve secrets with error handling
            self.tts_key = self._get_secret_safely(client, "tts-key").value
            self.ocr_key = self._get_secret_safely(client, "ocr-key").value
            self.language_key = self._get_secret_safely(client, "language-key").value
            self.gpt_key = self._get_secret_safely(client, "gpt-key").value
            self.database_key = self._get_secret_safely(client, "database-key").value

            print("✅ Set up KeyVault client and retrieved secrets successfully.")
        except Exception as e:
            print(f"❌ Failed to initialize KeyVault client or retrieve secrets: {e}")
            raise

    def _get_secret_safely(self, client, secret_name):
        """
        Safely retrieve a secret from Key Vault with error handling.
        """
        try:
            secret = client.get_secret(secret_name)
            if not secret.value:
                logger.warning(f"Secret '{secret_name}' is empty")
                return None
            print(f"✅ Successfully retrieved secret: {secret_name} 🎉")
            return secret
        except Exception as e:
            print(f"❌ Failed to retrieve secret '{secret_name}': {e} 😞")
            raise
