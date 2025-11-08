# Tool Permissions and Guidelines

This document defines allowed operations and tools for the AI assistant in this project.

## Allowed Operations

The AI assistant may use these tools/commands:

### Git Operations
- `git add`, `git commit`, `git push`, `git pull`
- `git branch`, `git checkout`, `git merge`, `git diff`, `git log`
- `git status`, `git show`

### Code Quality Tools
- `ruff check` - Lint Python code
- `ruff format` - Format Python code
- `ruff check --fix` - Auto-fix linting issues

### Testing Tools
- `python3 -m pytest` - Run pytest tests
- `uv run pytest` - Run pytest via uv
- `pytest` - Run pytest directly

### Development Tools
- `python`, `python3` - Python interpreters
- `uv` - Python package manager
- `gh` - GitHub CLI
- `source` - Source shell scripts for environment setup

### File Operations
- `tree` - Directory listing

### Web Operations
- Web fetching (for documentation, API references, etc.)

## Denied Operations

None currently - all operations are allowed.

## Usage Guidelines

### Before Committing Code
1. Always run `ruff format` to auto-format code
2. Always run `ruff check --fix` to auto-fix correctable issues
3. Always run `ruff check` to verify zero violations
4. Manually resolve any remaining violations before marking code complete

### Code Quality Gates
- Code is NOT complete until `ruff check` reports ZERO violations
- Complexity violations (C901, PLR0915) must be refactored
- Blind exception catching (BLE001) must use specific exception types
- All other violations must be resolved

### Testing
- Run tests before committing changes
- Use `uv run pytest` for consistency with project setup

## Notes

- These permissions are guidelines for the AI assistant
- The AI should naturally use these tools when appropriate
- Always verify tool output before proceeding
- When in doubt, ask the user before executing potentially destructive operations

