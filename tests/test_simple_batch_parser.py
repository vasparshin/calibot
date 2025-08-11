import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent

async def run_cases():
    agent = NLPAgent()
    cases = [
        ("add two lessons today at 5 and 7 pm", 2),
        ("create two events today one at 5 and one at 7pm", 2),
        ("schedule 3 meetings tomorrow at 9, 10 and 11", 3),
        ("schedule two calls in tonya's calendar at 14:00 and 16:00", 2),
    ]
    failures = 0
    for msg, expected_min in cases:
        result = await agent.extract_intent(msg, [])
        intent = result.get("intent")
        events = result.get("events") or []
        if intent != "batch_create" or len(events) < expected_min:
            print(f"FAIL: '{msg}' -> intent={intent}, events={len(events)} (expected >= {expected_min})")
            failures += 1
        else:
            print(f"OK: '{msg}' -> {len(events)} events parsed")
    return failures

def test_simple_batch_parser():
    failures = asyncio.run(run_cases())
    assert failures == 0, f"{failures} batch parser cases failed"

if __name__ == "__main__":
    test_simple_batch_parser()
