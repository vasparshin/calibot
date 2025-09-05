#!/usr/bin/env python3
"""
Migration Script for CaliBOT Optimization
Safely replaces the original routes.py with the optimized version.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

class MigrationPerformer:
    """Performs the actual migration from legacy to optimized architecture."""

    def __init__(self):
        self.backup_dir = f"backups/migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.project_root = Path(__file__).parent.parent

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def error(self, message: str):
        """Log error message."""
        self.log(message, 'ERROR')

    def success(self, message: str):
        """Log success message."""
        self.log(message, 'SUCCESS')

    def create_backup(self) -> bool:
        """Create backup of current system."""
        self.log("Creating backup of current system...")

        try:
            # Create backup directory
            backup_path = self.project_root / self.backup_dir
            backup_path.mkdir(parents=True, exist_ok=True)

            # Files to backup
            files_to_backup = [
                'backend/app/routes.py',
                'backend/app/api/',
                'backend/app/services/',
                'backend/app/agent/',
                'backend/app/utils/',
                'backend/app/config.py',
                'backend/app/main.py'
            ]

            for file_path in files_to_backup:
                src = self.project_root / file_path
                dst = backup_path / file_path

                if src.exists():
                    if src.is_file():
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        self.log(f"Backed up: {file_path}")
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        self.log(f"Backed up directory: {file_path}")

            # Create backup manifest
            manifest_path = backup_path / "MANIFEST.txt"
            with open(manifest_path, 'w') as f:
                f.write(f"Migration Backup Created: {datetime.now()}\n")
                f.write(f"Original routes.py backed up\n")
                f.write("Optimized architecture ready for deployment\n")

            self.success(f"Backup created successfully in: {self.backup_dir}")
            return True

        except Exception as e:
            self.error(f"Failed to create backup: {e}")
            return False

    def perform_migration(self) -> bool:
        """Perform the actual migration."""
        self.log("Performing migration to optimized architecture...")

        try:
            # Step 1: Replace routes.py with optimized version
            optimized_routes = self.project_root / "backend/app/routes_optimized.py"
            target_routes = self.project_root / "backend/app/routes.py"

            if optimized_routes.exists():
                shutil.copy2(optimized_routes, target_routes)
                self.success("Replaced routes.py with optimized version")
            else:
                self.error("Optimized routes file not found!")
                return False

            # Step 2: Update main.py if needed (check for any required changes)
            main_file = self.project_root / "backend/app/main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    main_content = f.read()

                # Check if we need to update imports
                if 'from app.api.routes import router' in main_content:
                    self.log("Main.py already has correct import")
                else:
                    self.log("Main.py import may need updating (manual check required)")

            # Step 3: Verify new structure
            required_dirs = [
                'backend/app/core',
                'backend/app/operations'
            ]

            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    self.error(f"Required directory missing: {dir_path}")
                    return False

            self.success("Migration completed successfully")
            return True

        except Exception as e:
            self.error(f"Migration failed: {e}")
            return False

    def rollback_migration(self) -> bool:
        """Rollback to previous version if needed."""
        self.log("Rolling back migration...")

        try:
            backup_path = self.project_root / self.backup_dir

            if not backup_path.exists():
                self.error("No backup found to rollback to!")
                return False

            # Restore routes.py
            backup_routes = backup_path / "backend/app/routes.py"
            target_routes = self.project_root / "backend/app/routes.py"

            if backup_routes.exists():
                shutil.copy2(backup_routes, target_routes)
                self.success("Rolled back routes.py")
            else:
                self.error("Backup routes.py not found!")
                return False

            self.success("Rollback completed successfully")
            return True

        except Exception as e:
            self.error(f"Rollback failed: {e}")
            return False

    def run_migration(self, perform_migration: bool = True) -> bool:
        """Run the complete migration process."""
        self.log("=" * 60)
        self.log("CALIBOT OPTIMIZATION MIGRATION")
        self.log("=" * 60)

        # Step 1: Create backup
        if not self.create_backup():
            self.error("Migration aborted due to backup failure")
            return False

        # Step 2: Perform migration if requested
        if perform_migration:
            if not self.perform_migration():
                self.error("Migration failed! Attempting rollback...")
                if self.rollback_migration():
                    self.success("Rollback successful - system restored")
                else:
                    self.error("Rollback failed! Manual intervention required!")
                return False

        # Step 3: Post-migration instructions
        self.display_post_migration_instructions()

        return True

    def display_post_migration_instructions(self):
        """Display instructions for after migration."""
        self.log("\n" + "=" * 60)
        self.log("POST-MIGRATION INSTRUCTIONS")
        self.log("=" * 60)

        instructions = [
            "1. Test the optimized system:",
            "   python scripts/migration_verification.py",
            "",
            "2. Run integration tests:",
            "   python tests/test_optimized_operations.py",
            "",
            "3. Test with real Telegram bot:",
            "   python tests/telegram_like_tester.py",
            "",
            "4. Monitor logs for any issues:",
            "   python scripts/render_api_logs.py",
            "",
            "5. If issues arise, rollback with:",
            "   python scripts/perform_migration.py --rollback",
            "",
            "6. Update version numbers:",
            "   - Update pyproject.toml version",
            "   - Update backend/app/__init__.py version",
            "   - Commit with format: 'vX.Y.Z: Optimized architecture migration'",
            "",
            "7. Deploy to production:",
            "   git push origin main",
            "",
            "8. Verify deployment:",
            "   python scripts/render_api_logs.py",
        ]

        for instruction in instructions:
            print(instruction)

        self.success("\n🎉 Migration preparation complete!")
        self.success("Follow the instructions above to complete the process.")

def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description='CaliBOT Optimization Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback to previous version')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    migrator = MigrationPerformer()

    if args.rollback:
        success = migrator.rollback_migration()
    elif args.dry_run:
        migrator.log("DRY RUN MODE - No changes will be made")
        migrator.display_post_migration_instructions()
        success = True
    else:
        success = migrator.run_migration()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
