#!/usr/bin/env python3
"""
Quick Test Setup - Sets up automated testing environment for Calibot.

This script helps you quickly set up and run comprehensive tests without manual intervention.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout.strip():
                print(f"📤 Output: {result.stdout.strip()}")
        else:
            print(f"❌ Failed with code {result.returncode}")
            if result.stderr.strip():
                print(f"📥 Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_environment():
    """Check if environment is properly set up."""
    print("🔍 Checking Environment")
    print("="*40)
    
    # Check Python
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required packages
    required_packages = ["aiohttp", "asyncio"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        install_cmd = f"pip install {' '.join(missing_packages)}"
        run_command(install_cmd, "Installing dependencies")
    
    return len(missing_packages) == 0

def test_local_backend():
    """Test if local backend is running."""
    print("\n🌐 Testing Local Backend")
    print("="*30)
    
    try:
        import aiohttp
        import asyncio
        
        async def check_backend():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/health", timeout=5) as response:
                        return response.status == 200
            except:
                return False
        
        is_running = asyncio.run(check_backend())
        
        if is_running:
            print("✅ Local backend is running on port 8000")
            return True
        else:
            print("❌ Local backend not accessible on port 8000")
            return False
            
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def run_quick_test():
    """Run a quick test to verify everything works."""
    print("\n⚡ Quick Test")
    print("="*20)
    
    # Test the direct API tester
    test_script = Path(__file__).parent / "direct_api_tester.py"
    
    if test_script.exists():
        print("✅ Direct API tester found")
        
        # Run a simple test
        choice = input("\nRun quick API test? (y/N): ").strip().lower()
        if choice == 'y':
            run_command(f"python {test_script}", "Running Direct API Test")
    else:
        print("❌ Direct API tester not found")

def main():
    """Main setup and testing flow."""
    print("🚀 CALIBOT TEST SETUP")
    print("="*50)
    
    # Step 1: Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment setup failed. Please fix issues and try again.")
        return
    
    # Step 2: Test local backend
    backend_running = test_local_backend()
    
    # Step 3: Show options
    print("\n📋 TESTING OPTIONS")
    print("="*30)
    print("1. 🏠 Test Local Backend (localhost:8000)")
    print("2. 🌐 Test Deployed Backend (Render)")
    print("3. 🤖 Set up Test Bot (requires manual setup)")
    print("4. ⚡ Quick API Test")
    print("5. 📊 Full Automated Test Suite")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        if backend_running:
            run_command("python direct_api_tester.py", "Testing Local Backend")
        else:
            print("❌ Local backend not running. Start it first:")
            print("💡 cd backend && uvicorn app.main:app --reload")
    
    elif choice == "2":
        backend_url = input("Enter your Render backend URL: ").strip()
        if backend_url:
            # Set environment variable and run test
            os.environ["BACKEND_URL"] = backend_url
            run_command("python direct_api_tester.py", f"Testing Deployed Backend: {backend_url}")
    
    elif choice == "3":
        print("\n🤖 Test Bot Setup")
        print("📖 Please follow the guide in CREATE_TEST_BOT.md")
        print("💡 After setup, you can use automated_test_bot.py")
    
    elif choice == "4":
        run_quick_test()
    
    elif choice == "5":
        print("\n📊 Full Test Suite")
        run_command("python automated_test_bot.py", "Running Full Automated Tests")
    
    else:
        print("❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
