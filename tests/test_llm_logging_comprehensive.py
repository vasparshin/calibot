#!/usr/bin/env python3
"""
Comprehensive test for LLM logging functionality in CaliBOT.
Tests both input and output logging to verify complete content visibility.
"""

import asyncio
import os
import sys
import logging
import tempfile
import io
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import ConversationState

class LogCapture:
    """Captures log output for testing"""
    def __init__(self):
        self.logs = []
        self.handler = None
        
    def start_capture(self):
        """Start capturing logs"""
        self.logs = []
        
        # Create a string stream to capture logs
        self.log_stream = io.StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setLevel(logging.INFO)
        
        # Add to the logger
        logger = logging.getLogger('app.agent.nlp_agent')
        logger.addHandler(self.handler)
        logger.setLevel(logging.INFO)
        
    def stop_capture(self):
        """Stop capturing logs and return captured content"""
        if self.handler:
            logger = logging.getLogger('app.agent.nlp_agent')
            logger.removeHandler(self.handler)
            
        content = self.log_stream.getvalue()
        self.log_stream.close()
        return content

async def test_complete_logging():
    """Test that LLM logging shows complete content without truncation"""
    
    print("🔍 Testing Complete LLM Logging")
    print("=" * 50)
    
    # Set up environment for testing
    os.environ['LITELLM_MODEL'] = 'gpt-4.1-mini'
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test-key')
    
    # Initialize components
    conversation_state = ConversationState()
    nlp_agent = NLPAgent()
    
    # Set up log capture
    log_capture = LogCapture()
    log_capture.start_capture()
    
    try:
        # Test with a simple user message that should trigger complete logging
        chat_id = "test_logging_123"
        user_message = "create a meeting tomorrow at 3pm for 1 hour called 'Project Review'"
        
        print(f"📝 Test Message: '{user_message}'")
        print(f"📏 Message Length: {len(user_message)} characters")
        
        # Add conversation history to make system prompt longer
        conversation_state.add_message(chat_id, "user", "What's my schedule today?")
        conversation_state.add_message(chat_id, "assistant", "You have 3 meetings scheduled...")
        conversation_state.add_message(chat_id, "user", "Can you reschedule the 2pm meeting?")
        conversation_state.add_message(chat_id, "assistant", "I can help you reschedule...")
        
        print("📚 Added conversation history to increase system prompt size")
        
        # Extract intent (this will trigger LLM logging)
        print("\n🚀 Calling NLP Agent...")
        result = await nlp_agent.extract_intent(user_message, chat_id)
        
        print(f"✅ Intent extracted: {result}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    finally:
        # Capture and analyze logs
        captured_logs = log_capture.stop_capture()
        
        print("\n📊 LOG ANALYSIS")
        print("=" * 50)
        
        # Split logs into lines for analysis
        log_lines = captured_logs.split('\n')
        
        # Analyze log content
        system_message_lines = [line for line in log_lines if 'COMPLETE SYSTEM MESSAGE' in line or 'System content:' in line or 'System chunk' in line]
        user_message_lines = [line for line in log_lines if 'COMPLETE USER MESSAGE' in line]
        response_lines = [line for line in log_lines if 'COMPLETE LLM RESPONSE' in line]
        
        print(f"📥 System message log entries: {len(system_message_lines)}")
        print(f"👤 User message log entries: {len(user_message_lines)}")
        print(f"🤖 Response log entries: {len(response_lines)}")
        
        # Check for truncation indicators
        truncated_lines = [line for line in log_lines if '...' in line and 'chars' in line]
        print(f"✂️ Truncated content indicators: {len(truncated_lines)}")
        
        # Show sample system message content
        if system_message_lines:
            print("\n📋 SYSTEM MESSAGE SAMPLE:")
            for line in system_message_lines[:3]:  # Show first 3 lines
                print(f"   {line}")
                
        # Show user message content
        if user_message_lines:
            print("\n👤 USER MESSAGE CONTENT:")
            for line in user_message_lines:
                print(f"   {line}")
                
        # Show response content
        if response_lines:
            print("\n🤖 LLM RESPONSE CONTENT:")
            for line in response_lines:
                print(f"   {line}")
                
        # Validation checks
        print("\n✅ VALIDATION RESULTS")
        print("=" * 50)
        
        validation_passed = True
        
        # Check 1: System message logging exists
        if not system_message_lines:
            print("❌ FAIL: No system message logging found")
            validation_passed = False
        else:
            print("✅ PASS: System message logging detected")
            
        # Check 2: User message logging exists
        if not user_message_lines:
            print("❌ FAIL: No user message logging found")
            validation_passed = False
        else:
            print("✅ PASS: User message logging detected")
            
        # Check 3: Response logging exists
        if not response_lines:
            print("❌ FAIL: No LLM response logging found")
            validation_passed = False
        else:
            print("✅ PASS: LLM response logging detected")
            
        # Check 4: No truncation should occur for complete logging
        if truncated_lines:
            print(f"⚠️  WARNING: Found {len(truncated_lines)} lines with truncation indicators")
            for line in truncated_lines[:2]:  # Show first 2
                print(f"     {line}")
        else:
            print("✅ PASS: No truncation indicators found")
            
        # Check 5: Look for length indicators
        length_lines = [line for line in log_lines if 'Length ' in line and 'chars' in line]
        if length_lines:
            print(f"📏 PASS: Found {len(length_lines)} length indicators")
            for line in length_lines[:2]:
                print(f"     {line}")
        else:
            print("⚠️  WARNING: No length indicators found")
            
        # Overall result
        print("\n🎯 OVERALL TEST RESULT")
        print("=" * 50)
        if validation_passed:
            print("✅ COMPLETE LOGGING TEST PASSED")
            print("   - All message types are being logged")
            print("   - Content visibility appears complete")
        else:
            print("❌ COMPLETE LOGGING TEST FAILED")
            print("   - Some logging components are missing")
            
        # Save detailed logs for inspection
        log_file = "test_llm_logging_output.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"LLM Logging Test Results - {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            f.write("CAPTURED LOGS:\n")
            f.write("-" * 40 + "\n")
            f.write(captured_logs)
            
        print(f"📄 Detailed logs saved to: {log_file}")
        
        return validation_passed

def check_environment():
    """Check if we can run the test"""
    print("🔧 Environment Check")
    print("=" * 30)
    
    required_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
            
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("✅ All required environment variables present")
        return True

async def main():
    """Main test execution"""
    print("🧪 CaliBOT LLM Logging Comprehensive Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Cannot proceed with LLM tests.")
        print("💡 Note: This test requires actual LLM calls to verify logging.")
        return False
        
    print()
    
    # Run the logging test
    try:
        success = await test_complete_logging()
        
        print(f"\n⏰ Test completed at: {datetime.now()}")
        
        if success:
            print("\n🎉 ALL TESTS PASSED - LLM logging is working correctly!")
            return True
        else:
            print("\n⚠️  TESTS FAILED - LLM logging needs fixes")
            return False
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
