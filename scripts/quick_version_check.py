#!/usr/bin/env python3
"""
Quick version check utility for CaliBOT deployment verification
"""

import requests
import json
from pathlib import Path

def quick_version_check():
    """Quick check of local vs deployed version"""
    
    # Get local version
    try:
        current_dir = Path.cwd()
        for path in [current_dir] + list(current_dir.parents):
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('version = '):
                            local_version = line.split('"')[1]
                            break
                break
        else:
            print("❌ Could not find pyproject.toml")
            return
    except Exception as e:
        print(f"❌ Error reading local version: {e}")
        return
    
    # Get deployed version
    try:
        response = requests.get("https://calibot-utq6.onrender.com/health", timeout=5)
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
    
    # Compare versions
    print(f"📦 Local:    {local_version}")
    print(f"🌐 Deployed: {deployed_version}")
    print(f"💚 Health:   {health}")
    
    if local_version == deployed_version:
        print("✅ MATCH - Ready for testing!")
    else:
        print("❌ MISMATCH - Need to restart/redeploy!")
        print("\nTo fix:")
        print("  python scripts/verify_deployment.py")

if __name__ == "__main__":
    quick_version_check()
