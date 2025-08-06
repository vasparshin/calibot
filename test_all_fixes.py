#!/usr/bin/env python3
"""
Comprehensive test suite for CaliBOT fixes.
Validates all improvements: batch events, context handling, calendar selection.
"""

import asyncio
import json
import sys
import os
import subprocess
sys.path.append('/workspaces/calibot/backend')

def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_subheader(title):
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")

async def run_test_script(script_name, description):
    """Run a test script and return success status"""
    print_subheader(f"Running {description}")
    try:
        result = subprocess.run([
            '/workspaces/calibot/.venv/bin/python', 
            script_name
        ], cwd='/workspaces/calibot', capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout[-500:])  # Show last 500 chars
            print("STDERR:", result.stderr[-500:])
            return False
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def main():
    print_header("CaliBOT Comprehensive Test Suite")
    print("Testing all fixes and improvements for batch events, context handling, and calendar selection")
    
    # Test scripts to run
    tests = [
        ("test_batch_events.py", "Batch Event Creation"),
        ("test_context_and_calendar_selection.py", "Context Handling & Calendar Selection"),
        ("test_calendar_context_memory.py", "Calendar Context Memory"),
        ("test_production_scenario.py", "Production Scenario Validation"),
    ]
    
    results = []
    
    for script, description in tests:
        success = await run_test_script(script, description)
        results.append((description, success))
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {description}")
    
    print(f"\nOverall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("CaliBOT is ready for production with improved:")
        print("  • Batch event creation with multiple JSON objects")
        print("  • Enhanced conversation context handling")
        print("  • Proper calendar name extraction and selection")
        print("  • Robust LLM response parsing")
        print("  • Context memory across conversation turns")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
