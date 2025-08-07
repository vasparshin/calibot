#!/usr/bin/env python3
"""
Version Control Demonstration for CaliBOT
==========================================

This script demonstrates the proper version control workflow 
according to the established rules.

Current Version Status Check:
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def check_version_sync():
    """Check version synchronization across all files"""
    
    print("🔍 CaliBOT Version Status Check")
    print("=" * 50)
    
    # Check pyproject.toml
    try:
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('version ='):
                    pyproject_version = line.split('=')[1].strip().strip('"')
                    print(f"📁 pyproject.toml: {pyproject_version}")
                    break
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        pyproject_version = "unknown"
    
    # Check __init__.py
    try:
        with open('backend/app/__init__.py', 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('__version__'):
                    init_version = line.split('=')[1].strip().strip('"').strip("'")
                    print(f"🐍 backend/app/__init__.py: {init_version}")
                    break
            else:
                init_version = "not found"
                print(f"❌ __version__ not found in __init__.py")
    except Exception as e:
        print(f"❌ Error reading __init__.py: {e}")
        init_version = "not found"
    
    # Check CHANGELOG.md for latest version
    try:
        with open('CHANGELOG.md', 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                if line.startswith('## [') and not 'Unreleased' in line:
                    changelog_version = line.split('[')[1].split(']')[0]
                    print(f"📋 CHANGELOG.md latest: {changelog_version}")
                    break
    except Exception as e:
        print(f"❌ Error reading CHANGELOG.md: {e}")
        changelog_version = "unknown"
    
    print("\n🔄 Version Synchronization Status:")
    
    if pyproject_version == init_version:
        print(f"✅ pyproject.toml ↔ __init__.py: {pyproject_version}")
    else:
        print(f"❌ Version mismatch: pyproject.toml ({pyproject_version}) ≠ __init__.py ({init_version})")
    
    print(f"📝 CHANGELOG shows development at: {changelog_version}")
    
    print("\n📋 Version Control Rules:")
    print("   1. pyproject.toml is the source of truth")
    print("   2. __init__.py must match pyproject.toml")
    print("   3. CHANGELOG.md tracks version history")
    print("   4. Always update all three files together")
    print("   5. Tag releases: git tag vX.Y.Z")
    
    print("\n🚀 Release Process:")
    print("   1. Update pyproject.toml version")
    print("   2. Update __init__.py __version__")
    print("   3. Move [Unreleased] to [X.Y.Z] with date in CHANGELOG")
    print("   4. Commit: 'chore: bump version to X.Y.Z'")
    print("   5. Tag: 'git tag vX.Y.Z'")

if __name__ == "__main__":
    check_version_sync()
