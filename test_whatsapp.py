"""
Test WhatsApp Integration
Quick test script to verify Twilio WhatsApp setup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.whatsapp_sender import get_whatsapp_sender
import config

def test_whatsapp_integration():
    """Test WhatsApp integration setup"""
    
    print("=" * 60)
    print("TESTING WHATSAPP INTEGRATION")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking Configuration...")
    print(f"   Account SID: {config.TWILIO_ACCOUNT_SID}")
    print(f"   Auth Token: {'*' * 20} (hidden)")
    print(f"   From Number: {config.TWILIO_WHATSAPP_FROM}")
    print(f"   Recipients: {config.WHATSAPP_RECIPIENTS}")
    
    # Initialize sender
    print("\n2. Initializing WhatsApp Sender...")
    sender = get_whatsapp_sender()
    
    if not sender.is_enabled():
        print("   ❌ ERROR: WhatsApp sender not enabled!")
        print("   Please check your Twilio credentials in config.py")
        return False
    
    print("   ✓ WhatsApp sender initialized successfully")
    
    # Test message sending (optional - uncomment to actually send)
    print("\n3. Testing Message Sending...")
    print("   Skipping actual send (uncomment code to test)")
    
    # Uncomment below to actually send a test message:
    """
    if config.WHATSAPP_RECIPIENTS:
        test_recipient = config.WHATSAPP_RECIPIENTS[0]
        print(f"   Sending test message to {test_recipient}...")
        
        result = sender.send_report_notification(
            to_number=test_recipient,
            date="2025-11-29",
            total_violations=5,
            report_filename="DressGuard_Report_20251129.xlsx"
        )
        
        if result.get('success'):
            print(f"   ✓ Test message sent successfully!")
            print(f"   Message SID: {result.get('message_sid')}")
        else:
            print(f"   ❌ Failed to send message: {result.get('error')}")
            return False
    """
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST COMPLETED")
    print("=" * 60)
    print("\nTo send a real test message:")
    print("1. Uncomment the code block in this script")
    print("2. Ensure you have verified your recipient number in Twilio")
    print("3. Run this script again")
    print("\nOr use the DressGuard UI:")
    print("- Start the app with 'uvicorn main:app --reload'")
    print("- Click 'Send Alerts' button in the Actions panel")
    
    return True


if __name__ == "__main__":
    try:
        success = test_whatsapp_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
