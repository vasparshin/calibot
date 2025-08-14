#!/usr/bin/env python3
"""
Master Multi-Event Testing Automation Script

COMPLETE AUTOMATED WORKFLOW FOR CALIBOT MULTI-EVENT TESTING:
- Verifies deployment status
- Runs comprehensive webhook testing with TestBot simulation
- Analyzes responses using Render API logs  
- Automatically fixes issues if detected
- Redeploys and retests until all scenarios pass
- No user input required - fully automated end-to-end testing

This is the main entry point that orchestrates the entire testing workflow.
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime

def print_header():
    """Print the main header"""
    print("[ROBOT] CALIBOT MULTI-EVENT TESTING AUTOMATION")
    print("=" * 80)
    print("[DART] COMPLETE AUTOMATED WORKFLOW:")
    print("   • Webhook testing with TestBot simulation in Telegram group")
    print("   • Render API log analysis for response validation")  
    print("   • Automatic issue detection and code fixing")
    print("   • GitHub deployment and version verification")
    print("   • Retest loop until all scenarios pass")
    print()
    print("[REPORT] TESTING SCENARIOS:")
    print("   • Multi-event delete with one-by-one progression")
    print("   • Multi-event creation with proper formatting")
    print("   • Multi-event updates with confirmation flow")
    print()
    print("🚫 NO USER INPUT REQUIRED - FULLY AUTOMATED")
    print("=" * 80)
    print()

async def verify_prerequisites():
    """Verify all prerequisites are met"""
    print("[CHECK] VERIFYING PREREQUISITES")
    print("-" * 40)
    
    checks = []
    
    # Check if backend is responding
    try:
        import requests
        response = requests.get("https://calibot-utq6.onrender.com/", timeout=10)
        backend_ok = response.status_code == 200
        version = response.json().get("version", "unknown") if backend_ok else "unknown"
        checks.append(("Backend Health", backend_ok, f"Version: {version}"))
    except Exception as e:
        checks.append(("Backend Health", False, f"Error: {e}"))
    
    # Check git status
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, timeout=10)
        git_clean = len(result.stdout.strip()) == 0
        checks.append(("Git Status", git_clean, "Clean" if git_clean else "Uncommitted changes"))
    except Exception as e:
        checks.append(("Git Status", False, f"Error: {e}"))
    
    # Check required files exist
    required_files = [
        "tests/comprehensive_multi_event_automation.py",
        "tests/auto_fix_retest_loop.py",
        "backend/app/api/routes.py",
        "BOT_RULES.md"
    ]
    
    for file_path in required_files:
        try:
            with open(file_path, "r") as f:
                file_exists = True
        except:
            file_exists = False
        checks.append((f"File: {file_path}", file_exists, "Found" if file_exists else "Missing"))
    
    # Display results
    all_passed = True
    for check_name, passed, details in checks:
        status = "[CHECK]" if passed else "[X]"
        print(f"{status} {check_name}: {details}")
        if not passed:
            all_passed = False
    
    print()
    return all_passed

async def run_testing_workflow():
    """Run the comprehensive testing workflow"""
    print("[TEST_TUBE] RUNNING COMPREHENSIVE TESTING WORKFLOW")
    print("-" * 50)
    
    # First, try simple testing without auto-fix
    print("[ARROWS] Step 1: Initial comprehensive testing...")
    
    try:
        # Run the comprehensive test automation
        process = await asyncio.create_subprocess_exec(
            sys.executable, "tests/comprehensive_multi_event_automation.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("[CHECK] Initial testing completed successfully!")
            print("[CELEBRATION] All multi-event scenarios are working correctly.")
            return True
        else:
            print("[WARNING] Initial testing found issues - proceeding to auto-fix workflow...")
            
    except Exception as e:
        print(f"[X] Initial testing failed: {e}")
        print("[ARROWS] Proceeding to auto-fix workflow...")
    
    # If initial testing failed, run auto-fix loop
    print("\n[REPAIR] Step 2: Running auto-fix and retest loop...")
    
    try:
        # Run the auto-fix loop
        process = await asyncio.create_subprocess_exec(
            sys.executable, "tests/auto_fix_retest_loop.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("[CHECK] Auto-fix workflow completed successfully!")
            print("[CELEBRATION] All issues resolved and tests now passing.")
            return True
        else:
            print("[X] Auto-fix workflow could not resolve all issues.")
            print("Manual intervention may be required.")
            print("\nError details:")
            print(stderr.decode() if stderr else "No error details available")
            return False
            
    except Exception as e:
        print(f"[X] Auto-fix workflow failed: {e}")
        return False

def generate_summary_report():
    """Generate a summary of the testing session"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n[STATS] TESTING SESSION SUMMARY")
    print("=" * 50)
    print(f"[CLOCK] Completed: {timestamp}")
    print("[DART] Scenarios tested:")
    print("   • Multi-event delete with one-by-one progression")
    print("   • Multi-event creation with formatting validation")
    print("   • Multi-event updates with confirmation flow")
    print()
    print("[LINK] Integration points validated:")
    print("   • Webhook endpoint responses")
    print("   • TestBot visual messages in Telegram group")
    print("   • Render API log analysis")
    print("   • BOT_RULES.md compliance verification")
    print()
    print("[REPORT] Report files generated:")
    
    # List generated report files
    import glob
    test_reports = glob.glob("tests/multi_event_test_report_*.json")
    auto_fix_reports = glob.glob("tests/auto_fix_results_*.json")
    
    for report in sorted(test_reports + auto_fix_reports):
        print(f"   • {report}")
    
    print()

async def main():
    """Main execution orchestrator"""
    start_time = time.time()
    
    print_header()
    
    # Step 1: Verify prerequisites
    prereqs_ok = await verify_prerequisites()
    if not prereqs_ok:
        print("[X] Prerequisites check failed. Please resolve issues and try again.")
        return False
    
    print("[CHECK] All prerequisites verified - proceeding with testing workflow")
    print()
    
    # Step 2: Run the testing workflow  
    success = await run_testing_workflow()
    
    # Step 3: Generate summary
    elapsed_time = int(time.time() - start_time)
    generate_summary_report()
    
    print(f"[TIME] Total execution time: {elapsed_time} seconds")
    
    if success:
        print("\n[CELEBRATION] TESTING AUTOMATION COMPLETED SUCCESSFULLY!")
        print("[CHECK] CaliBOT multi-event scenarios are working correctly")
        print("[CHECK] All webhook integrations validated")
        print("[CHECK] TestBot simulation successful")
        print("[CHECK] BOT_RULES.md compliance verified")
    else:
        print("\n[WARNING] TESTING AUTOMATION COMPLETED WITH ISSUES")
        print("[X] Some scenarios may still have problems")
        print("[REPORT] Check generated report files for details")
        print("[REPAIR] Manual investigation may be required")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        
        print("\n" + "=" * 80)
        if success:
            print("[DART] MISSION ACCOMPLISHED: All multi-event scenarios validated")
        else:
            print("[DART] MISSION INCOMPLETE: Manual intervention required")
        print("=" * 80)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] Unexpected error in testing automation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
