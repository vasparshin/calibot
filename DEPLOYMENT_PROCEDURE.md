# CaliBOT Deployment Procedure

## Stable Deployment Process

Based on experience, here's the reliable procedure for ensuring deployments work:

### 1. Version Synchronization Issues
**Problem**: Multiple version declarations or cache issues prevent version updates.

**Solution**:
1. Ensure ONLY ONE `__version__` declaration in `backend/app/__init__.py`
2. Version must match exactly in:
   - `pyproject.toml` (line 3: `version = "X.Y.Z"`)
   - `backend/app/__init__.py` (`__version__ = "X.Y.Z"`)
   - `CHANGELOG.md` (header: `## [X.Y.Z] - YYYY-MM-DD`)

### 2. Render Deployment Trigger
**Problem**: Render may not auto-deploy or may deploy from cache.

**Solution**:
1. Always commit ALL changes first
2. Use: `git commit --allow-empty -m "force deploy vX.Y.Z - description"`
3. Push: `git push origin main`
4. Wait 3-4 minutes for build and deployment

### 3. Verification Process
**Problem**: Manual input prompts block automation.

**Solution** - Use improved `verify_deployment.py`:
- No user input required
- Auto-waits for deployment
- Auto-forces deployment if needed
- Uses correct root endpoint `/` instead of `/health`

### 4. Deployment Status Monitoring
**Use `recent_logs.py` to monitor**:
```bash
python scripts/recent_logs.py
```

**Key indicators**:
- `==> Cloning from https://github.com/vasparshin/calibot` - New deployment started
- `==> Your service is live 🎉` - Deployment completed
- `INFO:app.main:CaliBOT vX.Y.Z starting up` - Version confirmation

### 5. Version Check
**Endpoint**: `https://calibot-utq6.onrender.com/`
**Response**: `{"message":"CaliBOT - AI Calendar Bot is running","version":"X.Y.Z","status":"operational"}`

### 6. Common Issues

**Issue**: Version shows old number despite new code
**Cause**: Duplicate `__version__` declarations
**Fix**: Ensure only ONE declaration in `__init__.py`

**Issue**: 404 errors during deployment
**Cause**: Service restarting
**Fix**: Wait 2-3 minutes, service will be back

**Issue**: Deployment doesn't trigger
**Cause**: Render caching or no significant changes
**Fix**: Force with empty commit

### 7. Automated Deployment Command
```bash
# Complete deployment with verification
python scripts/verify_deployment.py
```

This command:
1. Checks current version
2. Auto-waits if needed
3. Forces deployment if required
4. Verifies final deployment
5. NO user input required

## Testing Queue Progression Fix

Once v0.1.126 is deployed, test with:
1. "move last 2 events" - should trigger one-by-one workflow
2. First response should show proper event name (not "ANY")
3. Second response should show "UPDATE Event 2 of 2" with next event details
4. Use webhook testing for comprehensive validation

## Integration with PROJECT_RULES.md

This procedure ensures:
- No manual intervention needed
- Proper version tracking
- Reliable deployment verification
- Clean testing workflow
