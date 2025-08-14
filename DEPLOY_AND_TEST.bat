@echo off
REM Automated deployment and testing for CaliBOT version 0.1.123
echo.
echo ======================================================================
echo   CALIBOT DEPLOYMENT AND TESTING AUTOMATION
echo ======================================================================
echo.
echo Current Status:
echo   Local Version:    0.1.123 (one-by-one fixes ready)
echo   Deployed Version: 0.1.119 (outdated)
echo   Action Required:  Deploy latest version then test
echo.

echo Step 1: Committing and pushing changes...
git add .
git commit -m "v0.1.123: Deploy one-by-one workflow fixes and testing infrastructure"
git push origin main

echo.
echo Step 2: Waiting for Render deployment (3 minutes)...
timeout /t 180 /nobreak

echo.
echo Step 3: Verifying deployment...
python scripts/verify_deployment.py

echo.
echo Step 4: Running one-by-one workflow tests...
python tests/comprehensive_one_by_one_test.py

echo.
echo ======================================================================
echo   DEPLOYMENT AND TESTING COMPLETE
echo ======================================================================
echo.
echo Next Steps:
echo   1. Check test results above
echo   2. If tests pass, one-by-one workflow is working correctly
echo   3. If tests fail, review logs and fix issues
echo.
pause
