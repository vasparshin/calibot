# CaliBOT Scripts

This folder contains essential utility scripts for the CaliBOT project. All broken and duplicate scripts have been removed as per .cursorrules.

## 🟢 Working Scripts (Use These)

### 📊 Log Analysis
- **`render_api_logs.py`** - **PRIMARY LOG TOOL** (PowerShell compatible, no Unicode issues)
  ```bash
  python scripts/render_api_logs.py                    # Recent activity
  python scripts/render_api_logs.py intent create     # Filter terms
  python scripts/render_api_logs.py error             # Errors only
  ```

### 🚀 Deployment Management
- **`verify_deployment.py`** - Comprehensive deployment verification and service management
- **`pull_deployment_logs.py`** - Automated log collection and archiving

### 🧪 Testing Support  
- **`verify_test_group.py`** - Verify test group configuration for B2B demos

### 🗂️ Project Management
- **`organize_files.sh`** - Move misplaced test files to proper locations
- **`push_to_github.sh`** - GitHub automation with CHANGELOG.md integration

## 🚨 Script Categories (Removed)

### Broken Tools (Deleted per .cursorrules)
- ❌ `recent_logs.py` - Unicode errors in PowerShell  
- ❌ `quick_version_check.py` - 404 errors
- ❌ All streaming scripts (`live_logs.py`, `stream_logs.*`) - Get stuck

### Duplicates (Consolidated)
- ❌ 10+ log analysis variants → Use `render_api_logs.py`
- ❌ Multiple API test scripts → Exploration complete
- ❌ Duplicate deployment checks → Use `verify_deployment.py`
- ❌ Git automation variants → Use `push_to_github.sh`

## 📋 Usage Guidelines

### Before Running Scripts
1. **Set Environment**: Ensure `RENDER_API_KEY` is set
2. **Navigate to Project**: Always `cd calibot` first
3. **Check Dependencies**: Python 3.8+ with `requests` library

### Script Execution
```bash
# Navigate to project root first
cd calibot

# Log analysis (primary tool)
python scripts/render_api_logs.py

# Deployment verification
python scripts/verify_deployment.py

# Test group verification for B2B demos
python scripts/verify_test_group.py
```

### Best Practices
- **Always use `render_api_logs.py`** for log analysis
- **Verify deployment** before testing with `verify_deployment.py`
- **Use proper group ID** (`-4627994150`) for real testing
- **Check .cursorrules** for latest tool classifications

## 🔧 Environment Setup

### Required Environment Variables
```bash
export RENDER_API_KEY="your_render_api_key"
```

### Service Configuration (Hardcoded)
- **Service ID**: `srv-d1vqbkp5pdvs73echbeg`
- **Owner ID**: `tea-kks41ij4d82bpujdqv0g`
- **Backend URL**: `https://calibot-utq6.onrender.com`

---

**Total Scripts**: 7 essential scripts (from 33 original scripts)
**Duplicates Removed**: 20+ redundant scripts  
**Broken Scripts Removed**: 6+ problematic scripts
**Maintainability**: ✅ Improved - Clear purpose, no confusion