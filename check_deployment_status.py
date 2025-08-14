#!/usr/bin/env python3
"""
Simple deployment status check and action recommendation
"""

import requests
import json
from pathlib import Path

def main():
    print("🔍 CALIBOT DEPLOYMENT STATUS CHECK")
    print("="*50)
    
    # Get local version
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            for line in f:
                if line.strip().startswith('version = '):
                    local_version = line.split('"')[1]
                    break
    else:
        print("❌ pyproject.toml not found")
        return
    
    # Get deployed version
    try:
        response = requests.get("https://calibot-utq6.onrender.com/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            deployed_version = data.get('version', 'unknown')
            health = data.get('status', 'unknown')
        else:
            print(f"❌ Backend error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Status report
    print(f"📦 Local Version:    {local_version}")
    print(f"🌐 Deployed Version: {deployed_version}")
    print(f"💚 Health Status:    {health}")
    print()
    
    if local_version == deployed_version:
        print("✅ VERSIONS MATCH - Ready for testing!")
        print()
        print("🧪 Recommended Action:")
        print("   python tests/comprehensive_one_by_one_test.py")
    else:
        print("❌ VERSION MISMATCH - Deployment needed!")
        print()
        print("🚀 Required Actions:")
        print("   1. git add . && git commit -m 'v0.1.123: Deploy latest fixes'")
        print("   2. git push origin main")
        print("   3. Wait 3 minutes for auto-deployment")
        print("   4. python scripts/verify_deployment.py")
        print("   5. python tests/comprehensive_one_by_one_test.py")
        print()
        print("⚠️  CRITICAL: Testing the old version (0.1.119) won't validate")
        print("    the one-by-one fixes that are in version 0.1.123!")

if __name__ == "__main__":
    main()
