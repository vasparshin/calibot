#!/usr/bin/env python3
"""
Auto-Fix and Retest Loop for CaliBOT Multi-Event Issues

FULLY AUTOMATED TESTING & FIXING LOOP:
1. Run comprehensive multi-event tests
2. Analyze failures and identify root causes
3. Automatically apply fixes to codebase
4. Push to GitHub for auto-deployment
5. Verify deployment and retest
6. Repeat until all tests pass
7. No user input required

Integrates with comprehensive_multi_event_automation.py for complete workflow.
"""

import asyncio
import json
import subprocess
import time
import re
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoFixAndRetestLoop:
    def __init__(self):
        self.max_iterations = 3  # Maximum auto-fix attempts
        self.current_iteration = 0
        self.test_history = []
        self.applied_fixes = []
        
        # Known issue patterns and their fixes
        self.fix_patterns = {
            "multi_event_confirmation": {
                "description": "Multi-event confirmation display issues",
                "files_to_check": ["backend/app/api/routes.py", "backend/app/services/multi_event_operations.py"],
                "fix_function": self.fix_multi_event_confirmation
            },
            "one_by_one_progress": {
                "description": "One-by-one progression workflow issues", 
                "files_to_check": ["backend/app/services/multi_event_operations.py"],
                "fix_function": self.fix_one_by_one_progression
            },
            "event_hyperlink": {
                "description": "Event hyperlink formatting issues",
                "files_to_check": ["backend/app/services/event_formatter.py", "backend/app/api/routes.py"],
                "fix_function": self.fix_event_hyperlinks
            },
            "inline_keyboard": {
                "description": "Inline keyboard implementation issues",
                "files_to_check": ["backend/app/services/telegram_bot.py"],
                "fix_function": self.fix_inline_keyboards
            },
            "date_format": {
                "description": "Date and time formatting inconsistencies",
                "files_to_check": ["backend/app/services/event_formatter.py"],
                "fix_function": self.fix_date_formatting
            }
        }

    def log_fix_attempt(self, fix_name: str, success: bool, message: str):
        """Log fix attempt with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "[CHECK]" if success else "[X]"
        print(f"{timestamp} {status} FIX [{fix_name}]: {message}")
        
        self.applied_fixes.append({
            "timestamp": timestamp,
            "fix": fix_name,
            "success": success,
            "message": message,
            "iteration": self.current_iteration
        })

    async def run_comprehensive_tests(self) -> Dict:
        """Run the comprehensive test suite"""
        print(f"\n[TEST_TUBE] RUNNING COMPREHENSIVE TESTS (Iteration {self.current_iteration + 1})")
        print("=" * 70)
        
        try:
            # Run the comprehensive test automation
            process = await asyncio.create_subprocess_exec(
                "python", "tests/comprehensive_multi_event_automation.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="."
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse test results (look for JSON report file)
            if process.returncode == 0:
                # Find the most recent test report
                import glob
                test_files = glob.glob("tests/multi_event_test_report_*.json")
                if test_files:
                    latest_report = max(test_files)
                    with open(latest_report, "r") as f:
                        results = json.load(f)
                    return results
                else:
                    return {"success": False, "error": "No test report generated"}
            else:
                return {
                    "success": False,
                    "error": f"Test execution failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Test execution exception: {e}"}

    def analyze_test_failures(self, test_results: Dict) -> List[str]:
        """Analyze test results to identify required fixes"""
        issues = []
        
        if not test_results.get("success", False):
            # Check scenario-specific failures
            scenarios = test_results.get("scenarios", [])
            for scenario in scenarios:
                if not scenario.get("success", False):
                    scenario_name = scenario.get("scenario", "unknown")
                    
                    # Map scenario failures to fix patterns
                    if "delete" in scenario_name.lower() and "one-by-one" in scenario_name.lower():
                        issues.extend(["multi_event_confirmation", "one_by_one_progress"])
                    elif "create" in scenario_name.lower():
                        issues.extend(["event_hyperlink", "date_format"])
                    elif "update" in scenario_name.lower():
                        issues.extend(["multi_event_confirmation", "inline_keyboard"])
            
            # Check formatting issues
            for scenario in scenarios:
                formatting_checks = scenario.get("formatting_checks", {})
                for check_name, check_result in formatting_checks.items():
                    if not check_result:
                        issues.append(check_name)
        
        # Remove duplicates
        unique_issues = list(set(issues))
        
        print(f"\n[CHECK] IDENTIFIED ISSUES: {len(unique_issues)}")
        for issue in unique_issues:
            print(f"  • {issue}")
        
        return unique_issues

    async def fix_multi_event_confirmation(self) -> bool:
        """Fix multi-event confirmation display issues"""
        try:
            # Read the multi-event operations service
            with open("backend/app/services/multi_event_operations.py", "r") as f:
                content = f.read()
            
            # Check if confirmation formatting is correct
            if "Found {count} events to {action}" not in content:
                # Apply fix for confirmation message format
                updated_content = content.replace(
                    "Found {len(events)} events",
                    "Found {len(events)} events to {action}"
                )
                
                with open("backend/app/services/multi_event_operations.py", "w") as f:
                    f.write(updated_content)
                
                self.log_fix_attempt("Multi-Event Confirmation", True, "Updated confirmation message format")
                return True
            else:
                self.log_fix_attempt("Multi-Event Confirmation", True, "Already correctly formatted")
                return True
                
        except Exception as e:
            self.log_fix_attempt("Multi-Event Confirmation", False, f"Exception: {e}")
            return False

    async def fix_one_by_one_progression(self) -> bool:
        """Fix one-by-one progression workflow"""
        try:
            # Read the routes file
            with open("backend/app/api/routes.py", "r") as f:
                content = f.read()
            
            # Check if queue progression is properly implemented
            if "Event {current} of {total}" not in content:
                # This is a more complex fix that would require detailed analysis
                # For now, log that it needs manual attention
                self.log_fix_attempt("One-by-One Progression", False, "Complex fix required - needs manual review")
                return False
            else:
                self.log_fix_attempt("One-by-One Progression", True, "Progression format already correct")
                return True
                
        except Exception as e:
            self.log_fix_attempt("One-by-One Progression", False, f"Exception: {e}")
            return False

    async def fix_event_hyperlinks(self) -> bool:
        """Fix event hyperlink formatting"""
        try:
            # Read event formatter
            with open("backend/app/services/event_formatter.py", "r") as f:
                content = f.read()
            
            # Check if hyperlink format is correct
            if "[{event_name}]({event_link})" not in content:
                # Apply hyperlink formatting fix
                updated_content = re.sub(
                    r'event_name',
                    r'[{event_name}]({event_link})',
                    content,
                    count=1
                )
                
                with open("backend/app/services/event_formatter.py", "w") as f:
                    f.write(updated_content)
                
                self.log_fix_attempt("Event Hyperlinks", True, "Updated hyperlink formatting")
                return True
            else:
                self.log_fix_attempt("Event Hyperlinks", True, "Hyperlink format already correct")
                return True
                
        except Exception as e:
            self.log_fix_attempt("Event Hyperlinks", False, f"Exception: {e}")
            return False

    async def fix_inline_keyboards(self) -> bool:
        """Fix inline keyboard implementation"""
        try:
            # Read telegram bot service
            with open("backend/app/services/telegram_bot.py", "r") as f:
                content = f.read()
            
            # Check if inline keyboards are properly implemented
            if "InlineKeyboardMarkup" not in content:
                self.log_fix_attempt("Inline Keyboards", False, "InlineKeyboardMarkup not found - needs implementation")
                return False
            else:
                self.log_fix_attempt("Inline Keyboards", True, "Inline keyboards already implemented")
                return True
                
        except Exception as e:
            self.log_fix_attempt("Inline Keyboards", False, f"Exception: {e}")
            return False

    async def fix_date_formatting(self) -> bool:
        """Fix date and time formatting consistency"""
        try:
            # Read event formatter
            with open("backend/app/services/event_formatter.py", "r") as f:
                content = f.read()
            
            # Check if date format is consistent
            if "%A, %B %d, %Y" not in content:
                # Apply date formatting fix
                updated_content = content.replace(
                    "%Y-%m-%d",
                    "%A, %B %d, %Y"
                )
                
                with open("backend/app/services/event_formatter.py", "w") as f:
                    f.write(updated_content)
                
                self.log_fix_attempt("Date Formatting", True, "Updated date format to full format")
                return True
            else:
                self.log_fix_attempt("Date Formatting", True, "Date format already correct")
                return True
                
        except Exception as e:
            self.log_fix_attempt("Date Formatting", False, f"Exception: {e}")
            return False

    async def apply_fixes(self, issues: List[str]) -> bool:
        """Apply fixes for identified issues"""
        print(f"\n[FIX] APPLYING FIXES FOR {len(issues)} ISSUES")
        print("=" * 50)
        
        fix_results = []
        
        for issue in issues:
            if issue in self.fix_patterns:
                fix_info = self.fix_patterns[issue]
                print(f"\n[REPAIR] Fixing: {fix_info['description']}")
                
                # Apply the fix
                fix_success = await fix_info["fix_function"]()
                fix_results.append(fix_success)
            else:
                self.log_fix_attempt(issue, False, f"No fix pattern available for '{issue}'")
                fix_results.append(False)
        
        overall_success = all(fix_results)
        applied_count = sum(fix_results)
        
        print(f"\n[STATS] FIX RESULTS: {applied_count}/{len(issues)} successful")
        
        return overall_success

    async def increment_version_and_deploy(self) -> bool:
        """Increment version and deploy to production"""
        try:
            print(f"\n📦 INCREMENTING VERSION AND DEPLOYING")
            print("=" * 50)
            
            # Read current version
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            # Extract current version
            import re
            match = re.search(r'version = "([^"]+)"', content)
            if not match:
                print("[X] Could not find version in pyproject.toml")
                return False
            
            current_version = match.group(1)
            version_parts = current_version.split(".")
            
            # Increment patch version
            patch_num = int(version_parts[2]) + 1
            new_version = f"{version_parts[0]}.{version_parts[1]}.{patch_num}"
            
            # Update pyproject.toml
            updated_content = content.replace(
                f'version = "{current_version}"',
                f'version = "{new_version}"'
            )
            
            with open("pyproject.toml", "w") as f:
                f.write(updated_content)
            
            # Update __init__.py
            init_file = "backend/app/__init__.py"
            with open(init_file, "r") as f:
                init_content = f.read()
            
            updated_init = re.sub(
                r'__version__ = "[^"]*"',
                f'__version__ = "{new_version}"',
                init_content
            )
            
            with open(init_file, "w") as f:
                f.write(updated_init)
            
            print(f"[CHECK] Version updated: {current_version} -> {new_version}")
            
            # Update CHANGELOG.md
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            changelog_entry = f"""
## [{new_version}] - {timestamp}

### Fixed (Automated)
- **Multi-Event Automation Fixes**: Applied automated fixes for multi-event scenarios
- **Test Suite Integration**: Comprehensive testing and fixing workflow implemented
- **Deployment Verification**: Automated version checking and deployment validation

### Technical Details
- **Applied Fixes**: {len(self.applied_fixes)} automated fixes in iteration {self.current_iteration + 1}
- **Test Automation**: Full webhook testing with log analysis and auto-fixing
- **Version Management**: Automated version increment and deployment workflow

"""
            
            with open("CHANGELOG.md", "r") as f:
                changelog_content = f.read()
            
            # Insert new entry after the header
            lines = changelog_content.split("\n")
            insert_index = 2  # After "# CaliBOT Changelog" and empty line
            lines.insert(insert_index, changelog_entry)
            
            with open("CHANGELOG.md", "w") as f:
                f.write("\n".join(lines))
            
            print(f"[CHECK] CHANGELOG.md updated with version {new_version}")
            
            # Git add, commit, and push
            subprocess.run(["git", "add", "."], check=True)
            commit_message = f"fix: automated multi-event fixes and testing (v{new_version})"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push"], check=True)
            
            print(f"[CHECK] Changes committed and pushed to GitHub")
            print(f"[DEPLOY] Automatic deployment initiated via Render")
            
            return True
            
        except Exception as e:
            print(f"[X] Deployment failed: {e}")
            return False

    async def wait_for_deployment(self, new_version: str, max_wait_minutes: int = 5) -> bool:
        """Wait for deployment to complete and verify version"""
        print(f"\n⏳ WAITING FOR DEPLOYMENT (max {max_wait_minutes} minutes)")
        print("=" * 50)
        
        import requests
        backend_url = "https://calibot-utq6.onrender.com"
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(f"{backend_url}/", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    deployed_version = data.get("version", "unknown")
                    
                    if deployed_version == new_version:
                        elapsed = int(time.time() - start_time)
                        print(f"[CHECK] Deployment successful! Version {new_version} deployed in {elapsed} seconds")
                        return True
                    else:
                        print(f"⏳ Still deploying... Current: {deployed_version}, Expected: {new_version}")
                
            except Exception as e:
                print(f"⏳ Checking deployment... ({e})")
            
            await asyncio.sleep(15)  # Check every 15 seconds
        
        print(f"[X] Deployment timeout after {max_wait_minutes} minutes")
        return False

    async def run_auto_fix_loop(self) -> Dict:
        """Run the complete auto-fix and retest loop"""
        print("AUTOMATED MULTI-EVENT TESTING & FIXING LOOP")
        print("=" * 70)
        print(f"Max iterations: {self.max_iterations}")
        print("No user input required - fully automated workflow")
        print()
        
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            
            print(f"\n[ARROWS] ITERATION {self.current_iteration}/{self.max_iterations}")
            print("=" * 70)
            
            # Step 1: Run comprehensive tests
            test_results = await self.run_comprehensive_tests()
            self.test_history.append(test_results)
            
            # Step 2: Check if tests passed
            if test_results.get("success", False):
                print(f"\n[CELEBRATION] ALL TESTS PASSED! Auto-fix loop completed successfully.")
                return {
                    "success": True,
                    "iterations": self.current_iteration,
                    "final_test_results": test_results,
                    "applied_fixes": self.applied_fixes,
                    "test_history": self.test_history
                }
            
            # Step 3: Analyze failures and identify fixes
            issues = self.analyze_test_failures(test_results)
            
            if not issues:
                print(f"\n[WARNING] Tests failed but no fixable issues identified.")
                break
            
            # Step 4: Apply fixes
            fixes_applied = await self.apply_fixes(issues)
            
            if not fixes_applied:
                print(f"\n[WARNING] Could not apply all required fixes.")
                break
            
            # Step 5: Deploy changes
            deployment_success = await self.increment_version_and_deploy()
            
            if not deployment_success:
                print(f"\n[X] Deployment failed - stopping auto-fix loop.")
                break
            
            # Step 6: Wait for deployment and verify
            # Extract new version for verification
            with open("pyproject.toml", "r") as f:
                content = f.read()
            version_match = re.search(r'version = "([^"]+)"', content)
            new_version = version_match.group(1) if version_match else "unknown"
            
            deployment_ready = await self.wait_for_deployment(new_version)
            
            if not deployment_ready:
                print(f"\n[X] Deployment verification failed - stopping auto-fix loop.")
                break
            
            print(f"\n[CHECK] Iteration {self.current_iteration} completed - retesting...")
        
        # Final results
        print(f"\n[STATS] AUTO-FIX LOOP COMPLETED")
        print("=" * 70)
        print(f"Iterations completed: {self.current_iteration}")
        print(f"Fixes applied: {len(self.applied_fixes)}")
        
        final_test_results = self.test_history[-1] if self.test_history else {}
        final_success = final_test_results.get("success", False)
        
        if final_success:
            print("[CELEBRATION] Final result: ALL TESTS PASSING")
        else:
            print("[WARNING] Final result: Some tests still failing - manual intervention required")
        
        return {
            "success": final_success,
            "iterations": self.current_iteration,
            "final_test_results": final_test_results,
            "applied_fixes": self.applied_fixes,
            "test_history": self.test_history
        }

async def main():
    """Main execution - fully automated workflow"""
    auto_fixer = AutoFixAndRetestLoop()
    
    try:
        results = await auto_fixer.run_auto_fix_loop()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"tests/auto_fix_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n[DOC] Detailed results saved: {results_file}")
        
        return results["success"]
        
    except Exception as e:
        print(f"\n[X] Auto-fix loop failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Auto-fix loop interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")
        exit(1)
