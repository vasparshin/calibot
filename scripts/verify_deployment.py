#!/usr/bin/env python3
"""
Deployment Verification and Service Management Tool for CaliBOT

This script helps verify that the latest version is deployed and provides
utilities to restart the Render service if needed.
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "https://calibot-utq6.onrender.com"
ROOT_ENDPOINT = f"{BACKEND_URL}/"

def get_local_version():
    """Get the version from local pyproject.toml"""
    try:
        # Look for pyproject.toml in current directory or parent directories
        current_dir = Path.cwd()
        for path in [current_dir] + list(current_dir.parents):
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('version = '):
                            # Extract version from 'version = "0.1.121"'
                            return line.split('"')[1]
                break
        return None
    except Exception as e:
        print(f"❌ Error reading local version: {e}")
        return None

def get_deployed_version():
    """Get the version from deployed backend"""
    try:
        response = requests.get(ROOT_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('version'), data.get('status')
        else:
            print(f"❌ Backend returned status {response.status_code}")
            if response.status_code == 404:
                print("Response: {\"detail\":\"Not Found\"}")
            else:
                print(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Error checking deployed version: {e}")
        return None, None

def check_backend_health():
    """Check if backend is healthy and responsive"""
    print("🔍 Checking backend health...")
    
    try:
        response = requests.get(ROOT_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Status: {response.status_code}")
            print(f"✅ Version: {data.get('version', 'unknown')}")
            print(f"✅ Health: {data.get('status', 'unknown')}")
            return True, data.get('version')
        else:
            print(f"❌ Backend returned {response.status_code}")
            if response.status_code == 404:
                print("Response: {\"detail\":\"Not Found\"}")
            else:
                print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return False, None

def verify_deployment():
    """Verify that the latest local version matches deployed version"""
    print("🔍 Verifying deployment version...")
    
    local_version = get_local_version()
    if not local_version:
        print("❌ Could not determine local version")
        return False
    
    print(f"📦 Local version: {local_version}")
    
    deployed_version, health_status = get_deployed_version()
    if not deployed_version:
        print("❌ Could not determine deployed version")
        return False
    
    print(f"🌐 Deployed version: {deployed_version}")
    print(f"🌐 Health status: {health_status}")
    
    if local_version == deployed_version:
        print("✅ Version match! Deployment is up to date.")
        return True
    else:
        print("❌ Version mismatch! Deployment may be outdated.")
        print(f"Expected: {local_version}")
        print(f"Deployed: {deployed_version}")
        return False

def force_deployment():
    """Force a new deployment by creating an empty commit"""
    print("🚀 Forcing deployment via empty commit...")
    
    try:
        # Create empty commit
        result = subprocess.run([
            'git', 'commit', '--allow-empty', 
            '-m', 'Force deployment: trigger restart'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Git commit failed: {result.stderr}")
            return False
        
        print("✅ Empty commit created")
        
        # Push to trigger deployment
        result = subprocess.run([
            'git', 'push', 'origin', 'main'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Git push failed: {result.stderr}")
            return False
        
        print("✅ Pushed to origin/main - deployment triggered")
        print("⏳ Waiting 3 minutes for deployment...")
        
        # Wait for deployment
        for i in range(18):  # 18 * 10 seconds = 3 minutes
            time.sleep(10)
            print(f"⏳ Waiting... {(i+1)*10}/180 seconds")
        
        print("✅ Deployment wait complete")
        return True
        
    except Exception as e:
        print(f"❌ Error forcing deployment: {e}")
        return False

def main():
    """Main deployment verification workflow"""
    print("🚀 CaliBOT Deployment Verification Tool")
    print("=" * 50)
    
    # Step 1: Check backend health
    is_healthy, deployed_version = check_backend_health()
    
    if not is_healthy:
        print("\n❌ Backend is not healthy. Auto-deploying...")
        print("⚠️  Recent changes may still be deploying. Waiting first...")
        print("⏳ Waiting 2 minutes for current deployment...")
        time.sleep(120)
        
        # Check again after waiting
        is_healthy, deployed_version = check_backend_health()
        if not is_healthy:
            print("🚀 Backend still unhealthy, forcing deployment...")
            if force_deployment():
                print("\n🔄 Re-checking after forced deployment...")
                is_healthy, deployed_version = check_backend_health()
            else:
                print("❌ Force deployment failed")
                return 1
    
    print("\n" + "=" * 50)
    
    # Step 2: Verify version match
    version_match = verify_deployment()
    if version_match:
        print("\n🎉 Deployment verification successful!")
        print("✅ Backend is healthy and up to date")
        print("✅ Ready for testing!")
        return 0
    else:
        print("\n⚠️  Version mismatch detected!")
        print("This usually means Render auto-deployment failed or is still in progress.")
        print("🚀 Auto-deploying to sync versions...")
        
        if force_deployment():
            print("\n🔄 Re-verifying after forced deployment...")
            if verify_deployment():
                print("\n🎉 Deployment verification successful!")
                return 0
            else:
                print("\n❌ Version still mismatched after deployment")
                return 1
        else:
            print("❌ Force deployment failed")
            return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
