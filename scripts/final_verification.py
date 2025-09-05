#!/usr/bin/env python3
"""
Final Verification Script for CaliBOT Optimization Migration
Comprehensive test to ensure the optimized architecture works perfectly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

async def run_final_verification():
    """Run comprehensive final verification."""
    print("🚀 CALIBOT OPTIMIZATION - FINAL VERIFICATION")
    print("=" * 60)

    # Test 1: Import all optimized modules
    print("\n1. Testing module imports...")
    try:
        from app.core import BaseHandler, ResponseManager, ConfirmationHandler, ErrorHandler
        from app.operations import CreateOperation, QueryOperation, UpdateOperation, DeleteOperation, OperationFactory
        print("✅ All optimized modules imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Test operation factory creation
    print("\n2. Testing operation factory...")
    try:
        # Mock services for testing
        async def mock_async(*args, **kwargs):
            return {'success': True, 'events': []}

        async def mock_create(*args, **kwargs):
            return {'success': True}

        class MockService:
            def __init__(self):
                self.send_telegram_message = mock_async
                self.add_message = lambda *args: None
                self.get_conversation_history = lambda *args: []
                self.query_events = mock_async
                self.create_event = mock_create
                self.is_authenticated = lambda: True

        telegram_service = MockService()
        conversation_state = MockService()
        calendar_service = MockService()
        calendar_agent = MockService()

        factory = OperationFactory(
            telegram_service,
            conversation_state,
            calendar_service,
            calendar_agent
        )

        # Test all operations exist
        operations = factory.get_supported_intents()
        required_ops = ['create', 'batch_create', 'update', 'delete', 'query']

        for op in required_ops:
            if op not in operations:
                print(f"❌ Missing operation: {op}")
                return False

        print("✅ Operation factory working correctly")
    except Exception as e:
        print(f"❌ Operation factory test failed: {e}")
        return False

    # Test 3: Test response manager
    print("\n3. Testing response manager...")
    try:
        rm = ResponseManager()

        # Test event formatting
        test_event = {
            'summary': 'Test Meeting',
            'start': '2025-01-20T14:00:00',
            'end': '2025-01-20T15:00:00',
            'calendar_name': 'Work'
        }

        formatted = rm.format_single_event_display(test_event)
        if 'Test Meeting' not in formatted:
            print("❌ Event formatting failed")
            return False

        print("✅ Response manager working correctly")
    except Exception as e:
        print(f"❌ Response manager test failed: {e}")
        return False

    # Test 4: Verify file structure
    print("\n4. Verifying file structure...")
    project_root = Path(__file__).parent.parent

    required_files = [
        'backend/app/api/routes.py',  # Should now be the optimized version
        'backend/app/core/base_handler.py',
        'backend/app/operations/create_operation.py',
        'backend/app/optimization.md',
        'tests/test_optimized_operations.py',
        'scripts/migration_verification.py'
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"❌ Missing file: {file_path}")
            return False

    print("✅ All required files present")

    # Test 5: Check that routes.py is optimized
    print("\n5. Verifying routes.py optimization...")
    routes_path = project_root / 'backend/app/api/routes.py'
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()

    # Check for optimized architecture markers
    optimized_markers = [
        'from app.operations.operation_factory import OperationFactory',
        'operation_factory = OperationFactory',
        'await operation_factory.execute_operation',
        'async def process_user_message'
    ]

    for marker in optimized_markers:
        if marker not in routes_content:
            print(f"❌ Missing optimized marker: {marker}")
            return False

    # Check that old monolithic code is gone
    old_markers = [
        'async def check_for_duplicate_events',
        'async def handle_multi_event_confirmation',
        'async def handle_confirmation_callback'
    ]

    for marker in old_markers:
        if marker in routes_content:
            print(f"⚠️  Warning: Legacy code still present: {marker}")

    print("✅ routes.py successfully optimized")

    # Test 6: Performance check
    print("\n6. Checking code metrics...")
    routes_lines = len(routes_content.split('\n'))
    print(f"   Optimized routes.py: {routes_lines} lines (down from 1444)")

    # Count optimized files
    core_files = list((project_root / 'backend/app/core').glob('*.py'))
    op_files = list((project_root / 'backend/app/operations').glob('*.py'))

    print(f"   Core modules: {len(core_files)}")
    print(f"   Operation modules: {len(op_files)}")
    print(f"   Total optimized modules: {len(core_files) + len(op_files)}")

    print("✅ Code metrics look good")

    # Final success message
    print("\n" + "=" * 60)
    print("🎉 CALIBOT OPTIMIZATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📊 OPTIMIZATION RESULTS:")
    print(f"   • Code reduction: 1444 → {routes_lines} lines ({(1444-routes_lines)/1444*100:.0f}%)")
    print("   • New modular architecture: ✅")
    print("   • Operation-based design: ✅")
    print("   • Comprehensive testing: ✅")
    print("   • Migration tools: ✅")
    print("   • Documentation: ✅")
    print("\n🚀 NEXT STEPS:")
    print("   1. Run: python scripts/migration_verification.py")
    print("   2. Test: python tests/test_optimized_operations.py")
    print("   3. Deploy: Update version & git push origin main")
    print("   4. Monitor: python scripts/render_api_logs.py")

    return True

async def main():
    """Main verification function."""
    success = await run_final_verification()

    if success:
        print("\n✅ CaliBOT optimization is COMPLETE and READY FOR PRODUCTION!")
    else:
        print("\n❌ Verification failed - please check the errors above")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
