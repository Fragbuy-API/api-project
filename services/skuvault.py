import requests
from datetime import datetime
import logging
import json
from config import Config 

# Setup logging
logger = logging.getLogger(__name__)

class SkuVaultClient:
    """Client for interacting with the SkuVault API"""
    
    def __init__(self):
        self.api_url = Config.SKUVAULT_API_URL
        self.tenant_token = Config.SKUVAULT_TENANT_TOKEN
        self.user_token = Config.SKUVAULT_USER_TOKEN
        
        # Validate that credentials are available
        if not all([self.api_url, self.tenant_token, self.user_token]):
            logger.error("SkuVault API credentials are missing. Check environment variables.")
    
    def _get_headers(self):
        """Get headers required for SkuVault API calls"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Tenant-Token': self.tenant_token,
            'X-User-Token': self.user_token
        }
    
    def update_po_status(self, po_number, status):
        """
        Update a purchase order status in SkuVault
        
        Args:
            po_number: The purchase order number
            status: The new status of the purchase order
            
        Returns:
            dict: Response from the SkuVault API
        """
        if not all([self.api_url, self.tenant_token, self.user_token]):
            logger.error("Cannot update PO status: SkuVault API credentials are missing")
            return {
                "success": False,
                "error": "API credentials not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        endpoint = f"{self.api_url}/purchaseorders/status"
        
        # Map our status to SkuVault's expected status
        skuvault_status = "Closed" if status == "Complete" else "Open"
        
        payload = {
            "PONumber": po_number,
            "Status": skuvault_status
        }
        
        try:
            logger.info(f"Sending PO status update to SkuVault: PO={po_number}, Status={skuvault_status}")
            
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=10  # Set a reasonable timeout
            )
            
            # Check for successful response
            if response.status_code == 200:
                logger.info(f"Successfully updated PO {po_number} status in SkuVault")
                return {
                    "success": True,
                    "message": f"Successfully updated PO status to {skuvault_status} in SkuVault",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                except Exception:
                    error_message = f"HTTP error {response.status_code}"
                
                logger.error(f"SkuVault API error: {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error("SkuVault API request timed out")
            return {
                "success": False,
                "error": "API request timed out",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to SkuVault API")
            return {
                "success": False,
                "error": "Connection error",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error calling SkuVault API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }