# CaliBOT Changelog

CHANGELOG RULES - BE SPECIFIC AND TECHNICAL

## [0.1.183] - 2025-01-27

### DOCUMENTATION MODIFICATIONS

calibot/Project Docs/CHANGELOG_BACKUP_v0.1.182.md: Created backup of previous changelog (1668 lines)

.cursorrules: Consolidated PROJECT_RULES.md content into single source

calibot/tests/README.md: Updated references to .cursorrules

calibot/scripts/README.md: Updated references to .cursorrules

calibot/pyproject.toml: Version 0.1.182 → 0.1.183

calibot/backend/app/__init__.py: Version 0.1.182 → 0.1.183

## CHANGELOG STANDARDS (MANDATORY)

### AVOID Vague Statements:
- 'Fixed the issue' → INSTEAD: 'Updated GoogleCalendarService.query_events() to include q parameter for text search'
- 'Improved performance' → INSTEAD: 'Added Redis caching to reduce database queries by 40%'

### REQUIRED Format:
'[Component].[Method/Function/File]: [Specific Technical Change]'

### Impact Statements:
- Quantify changes: 'Reduced response time by 30%', 'Fixed 5 edge cases'
- Technical metrics: 'Decreased webhook processing from 2.1s to 0.8s'

### Version Format:
- Semantic versioning: X.Y.Z (Major.Minor.Patch)
- Major (X): Breaking changes, API changes
- Minor (Y): New features, enhancements
- Patch (Z): Bug fixes, documentation updates
