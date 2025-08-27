#!/usr/bin/env python3
"""
Migration Verification Script for CaliBOT Optimization
Verifies that the optimized architecture works correctly after migration.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class MigrationVerifier:
    """Verifies the optimized architecture works correctly."""

    def __init__(self):
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_total': 0,
            'errors': []
        }

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def error(self, message: str):
        """Log error message."""
        self.results['errors'].append(message)
        self.log(message, 'ERROR')

    def success(self, message: str):
        """Log success message."""
        self.log(message, 'SUCCESS')

    async def test_imports(self) -> bool:
        """Test that all optimized modules can be imported."""
        self.log("Testing optimized module imports...")

        try:
            # Test core modules
            from app.core.base_handler import BaseHandler
            from app.core.response_manager import ResponseManager
            from app.core.confirmation_handler import ConfirmationHandler
            from app.core.error_handler import ErrorHandler

            # Test operation modules
            from app.operations.base_operation import BaseOperation
            from app.operations.create_operation import CreateOperation
            from app.operations.query_operation import QueryOperation
            from app.operations.update_operation import UpdateOperation
            from app.operations.delete_operation import DeleteOperation
            from app.operations.operation_factory import OperationFactory

            self.success("All optimized modules imported successfully")
            return True

        except ImportError as e:
            self.error(f"Failed to import optimized modules: {e}")
            return False
        except Exception as e:
            self.error(f"Unexpected error during import test: {e}")
            return False

    async def test_operation_factory(self) -> bool:
        """Test that operation factory works correctly."""
        self.log("Testing operation factory...")

        try:
            from app.operations.operation_factory import OperationFactory

            # Create mock services (minimal for testing)
            class MockService:
                pass

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

            # Test supported intents
            intents = factory.get_supported_intents()
            expected_intents = ['create', 'batch_create', 'update', 'delete', 'query']

            for intent in expected_intents:
                if intent not in intents:
                    self.error(f"Missing intent in factory: {intent}")
                    return False

            self.success("Operation factory test passed")
            return True

        except Exception as e:
            self.error(f"Operation factory test failed: {e}")
            return False

    async def test_response_manager(self) -> bool:
        """Test response manager functionality."""
        self.log("Testing response manager...")

        try:
            from app.core.response_manager import ResponseManager

            rm = ResponseManager()

            # Test event formatting
            test_event = {
                'summary': 'Test Meeting',
                'start': '2025-01-20T14:00:00',
                'end': '2025-01-20T15:00:00',
                'calendar_name': 'Work Calendar'
            }

            formatted = rm.format_single_event_display(test_event)
            if 'Test Meeting' not in formatted:
                self.error("Event formatting failed")
                return False

            # Test event list formatting
            test_events = [test_event]
            list_formatted = rm.format_event_list_display(test_events)
            if 'Test Meeting' not in list_formatted:
                self.error("Event list formatting failed")
                return False

            self.success("Response manager test passed")
            return True

        except Exception as e:
            self.error(f"Response manager test failed: {e}")
            return False

    def check_file_structure(self) -> bool:
        """Check that optimized file structure exists."""
        self.log("Checking optimized file structure...")

        required_files = [
            'backend/app/core/__init__.py',
            'backend/app/core/base_handler.py',
            'backend/app/core/response_manager.py',
            'backend/app/core/confirmation_handler.py',
            'backend/app/core/error_handler.py',
            'backend/app/operations/__init__.py',
            'backend/app/operations/base_operation.py',
            'backend/app/operations/create_operation.py',
            'backend/app/operations/query_operation.py',
            'backend/app/operations/update_operation.py',
            'backend/app/operations/delete_operation.py',
            'backend/app/operations/operation_factory.py',
            'backend/app/routes_optimized.py',
            'backend/app/optimization.md'
        ]

        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        if missing_files:
            self.error(f"Missing optimized files: {missing_files}")
            return False

        self.success("Optimized file structure verified")
        return True

    def check_legacy_files(self) -> bool:
        """Check that legacy files still exist (for rollback)."""
        self.log("Checking legacy file availability...")

        legacy_files = [
            'backend/app/routes.py',  # Original routes file
            'backend/app/services/',  # Original services
            'backend/app/agent/',     # Original agents
        ]

        missing_legacy = []
        for file_path in legacy_files:
            if not os.path.exists(file_path):
                missing_legacy.append(file_path)

        if missing_legacy:
            self.error(f"Missing legacy files (rollback may not be possible): {missing_legacy}")
            return False

        self.success("Legacy files available for rollback")
        return True

    async def run_all_tests(self) -> bool:
        """Run all migration verification tests."""
        self.log("=" * 60)
        self.log("STARTING CALIBOT OPTIMIZATION MIGRATION VERIFICATION")
        self.log("=" * 60)

        tests = [
            ("File Structure Check", self.check_file_structure),
            ("Legacy Files Check", self.check_legacy_files),
            ("Import Test", self.test_imports),
            ("Operation Factory Test", self.test_operation_factory),
            ("Response Manager Test", self.test_response_manager),
        ]

        all_passed = True

        for test_name, test_func in tests:
            self.log(f"\n--- Running {test_name} ---")

            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                self.results['tests_passed'] += 1
            else:
                self.results['tests_failed'] += 1
                all_passed = False

            self.results['tests_total'] += 1

        # Summary
        self.log("\n" + "=" * 60)
        self.log("MIGRATION VERIFICATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.results['tests_passed']}")
        self.log(f"Tests Failed: {self.results['tests_failed']}")
        self.log(f"Total Tests: {self.results['tests_total']}")

        if self.results['errors']:
            self.log(f"\nErrors Encountered: {len(self.results['errors'])}")
            for error in self.results['errors']:
                self.log(f"  - {error}", "ERROR")

        if all_passed:
            self.success("\n🎉 MIGRATION VERIFICATION PASSED!")
            self.success("Optimized architecture is ready for deployment.")
        else:
            self.error("\n❌ MIGRATION VERIFICATION FAILED!")
            self.error("Please fix the issues before proceeding with deployment.")

        return all_passed

async def main():
    """Main verification function."""
    verifier = MigrationVerifier()
    success = await verifier.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
