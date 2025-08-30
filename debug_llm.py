#!/usr/bin/env python3
"""
Debug script to test LLM intent extraction for B2B test cases
"""
import asyncio
import json
import sys
import os

# Set required environment variables for testing
os.environ["LITELLM_MODEL"] = "gpt-4o-mini"  # Use a common model for testing
os.environ["OPENAI_API_KEY"] = "dummy_key"  # Won't actually call API in this test

# Add the backend to the path
sys.path.append('backend')

from app.agent.nlp_agent import NLPAgent

async def test_llm_responses():
    """Test LLM responses for failing B2B test cases"""
    agent = NLPAgent()

    test_cases = [
        "What events do I have tomorrow?",
        "Update the test meeting to 5pm",
        "Create lesson 1 at 8am and lesson 2 at 10am tomorrow",
        "Delete the delete test event",
        "Create event A at 1pm and event B at 3pm tomorrow"
    ]

    print("🔍 Testing LLM responses for failing B2B test cases:\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: '{test_case}'")
        try:
            result = await agent.extract_intent(test_case, [])
            print(f"LLM Response: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_llm_responses())
