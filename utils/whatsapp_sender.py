"""
WhatsApp Report Sender using WhatsApp Web (Direct from your phone)
No Twilio needed - uses your personal WhatsApp account
"""

import logging
from typing import Optional, Dict, Any
import requests
import os
import config

logger = logging.getLogger(__name__)


class WhatsAppSender:
    """
    Manages WhatsApp message sending via WhatsApp Web (your phone)
    Requires Node.js service running on localhost:3001
    """
    
    def __init__(self, service_url: str = None):
        """
        Initialize WhatsApp Web client connection
        
        Args:
            service_url: URL of the WhatsApp Web service (defaults to localhost:3001)
        """
        self.service_url = service_url or getattr(config, 'WHATSAPP_SERVICE_URL', 'http://localhost:3001')
        self._check_service()
    
    def _check_service(self):
        """Check if WhatsApp service is running"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("WhatsApp Web service is running")
            else:
                logger.warning("WhatsApp Web service returned unexpected status")
        except requests.exceptions.RequestException as e:
            logger.warning(f"WhatsApp Web service not available: {e}")
            logger.warning("Start service with: cd whatsapp-service && node server.js")
    
    def is_enabled(self) -> bool:
        """Check if WhatsApp Web service is ready"""
        try:
            response = requests.get(f"{self.service_url}/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get('connected', False)
            return False
        except:
            return False
    
    def send_message(self, to_number: str, message_body: str) -> Dict[str, Any]:
        """
        Send a simple text message via WhatsApp Web
        
        Args:
            to_number: Recipient WhatsApp number (e.g., '+919108816244' or '919108816244')
            message_body: Message text content
            
        Returns:
            Dict with status and message info
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'WhatsApp Web service not ready. Please start: cd whatsapp-service && node server.js'
            }
        
        # Clean phone number (remove + and spaces)
        clean_number = to_number.replace('+', '').replace(' ', '').replace('-', '')
        
        try:
            response = requests.post(
                f"{self.service_url}/send-message",
                json={
                    'to': clean_number,
                    'message': message_body
                },
                timeout=10
            )
            
            # Try to parse JSON response
            try:
                data = response.json()
            except ValueError as json_error:
                logger.error(f"Invalid JSON response from WhatsApp service: {response.text[:200]}")
                return {
                    'success': False,
                    'error': f"Invalid service response: {str(json_error)}"
                }
            
            if response.status_code == 200 and data.get('success'):
                logger.info(f"WhatsApp message sent successfully to {to_number}")
                return {
                    'success': True,
                    'to': to_number,
                    'message_sid': 'direct-wa-' + clean_number
                }
            else:
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"WhatsApp send failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp service connection error: {e}")
            return {
                'success': False,
                'error': f"Service unavailable: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_report_notification(self, to_number: str, date: str, total_violations: int, 
                                  report_filename: str = None) -> Dict[str, Any]:
        """
        Send a formatted violation report notification (text only)
        
        Args:
            to_number: Recipient WhatsApp number
            date: Report date (YYYY-MM-DD)
            total_violations: Number of violations detected
            report_filename: Optional filename for reference
            
        Returns:
            Dict with status and message info
        """
        # Format report message with the requested intro
        message = f"""Here are the non-compliance reports for today {date}

 *DressGuard Violation Report*

 Date: {date}
 Total Violations: {total_violations}

{" Report File: " + report_filename if report_filename else ""}

Please review the violations and take necessary action.

_Generated by DressGuard AI System_
        """.strip()
        
        return self.send_message(to_number, message)
    
    def send_report_with_file(self, to_number: str, date: str, total_violations: int,
                              report_path: str) -> Dict[str, Any]:
        """
        Send violation report with Excel file attachment via WhatsApp
        
        Args:
            to_number: Recipient WhatsApp number
            date: Report date (YYYY-MM-DD)
            total_violations: Number of violations detected
            report_path: Path to the Excel report file
            
        Returns:
            Dict with status and message info
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'WhatsApp Web service not ready. Please start: cd whatsapp-service && node server.js'
            }
        
        # Clean phone number
        clean_number = to_number.replace('+', '').replace(' ', '').replace('-', '')
        
        # Format message
        caption = f"""Here are the non-compliance reports for today {date}

 *DressGuard Violation Report*

 Date: {date}
 Total Violations: {total_violations}

Please review the attached Excel report.

_Generated by DressGuard AI System_"""
        
        try:
            # Read file and encode to base64
            import base64
            with open(report_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            filename = os.path.basename(report_path)
            
            response = requests.post(
                f"{self.service_url}/send-document",
                json={
                    'to': clean_number,
                    'caption': caption,
                    'filename': filename,
                    'filedata': file_data
                },
                timeout=30
            )
            
            # Try to parse JSON response
            try:
                data = response.json()
            except ValueError as json_error:
                logger.error(f"Invalid JSON response from WhatsApp service: {response.text[:200]}")
                return {
                    'success': False,
                    'error': f"Invalid service response: {str(json_error)}"
                }
            
            if response.status_code == 200 and data.get('success'):
                logger.info(f"WhatsApp report with file sent successfully to {to_number}")
                return {
                    'success': True,
                    'to': to_number,
                    'message_sid': 'direct-wa-doc-' + clean_number,
                    'file_sent': True
                }
            else:
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"WhatsApp file send failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp service connection error: {e}")
            return {
                'success': False,
                'error': f"Service unavailable: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp file: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
_whatsapp_sender = None

def get_whatsapp_sender() -> WhatsAppSender:
    """Get or create global WhatsApp sender instance"""
    global _whatsapp_sender
    if _whatsapp_sender is None:
        _whatsapp_sender = WhatsAppSender()
    return _whatsapp_sender
