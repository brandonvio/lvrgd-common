# Cursor Configuration Summary

This directory contains Cursor-specific configurations migrated from Claude Desktop artifacts.

## Files Created

### Core Configuration
- **`.cursor/rules/constitution.md`** - Project constitution (migrated from `.claude/constitution.md`)
  - Automatically read by Cursor AI assistant
  - **Auto-reloads on changes** (no restart needed)
  - Contains all 7 NON-NEGOTIABLE development principles
  - Reference in conversations: `@.cursor/rules/constitution.md`

### Documentation
- **`MIGRATION_GUIDE.md`** - Complete guide on how Claude artifacts map to Cursor
- **`TOOL_PERMISSIONS.md`** - Allowed tools and operations (from `settings.json`)
- **`WORKFLOWS.md`** - Common development workflows (from `commands/`)

### Instruction Templates
- **`INSTRUCTIONS/code-review.md`** - Code review workflow instructions
- **`INSTRUCTIONS/commit.md`** - Commit workflow instructions
- **`INSTRUCTIONS/task-execution.md`** - Task execution instructions
- **`INSTRUCTIONS/spec-generation.md`** - Specification generation instructions
- **`INSTRUCTIONS/task-generation.md`** - Task breakdown generation instructions

## Quick Start

### 1. Code Review
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md

Review all changes in the current branch compared to main.
```

### 2. Commit Changes
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/commit.md

Stage all changes, analyze them, generate a commit message, commit, and push.
```

### 3. Implement Feature
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-execution.md

Implement [feature description] following all constitutional principles.
```

### 4. Generate Specification
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/spec-generation.md

Generate a technical specification from @specs/[feature]-prompt.md
```

## Key Differences from Claude Desktop

| Claude Desktop | Cursor |
|----------------|--------|
| Slash commands (`/work`, `/commit`) | Manual prompts with instruction files |
| Multiple specialized agents | Single AI assistant with instruction templates |
| `settings.json` permissions | Documented in `TOOL_PERMISSIONS.md` |
| `constitution.md` | `.cursor/rules/constitution.md` (recommended, auto-reloads) |
| Agent definitions | Instruction templates in `INSTRUCTIONS/` |

## Usage Tips

1. **Always reference constitution** - Include `@.cursor/rules/constitution.md` in important conversations
2. **Combine instructions** - Reference multiple files: `@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md`
3. **Use workflows** - See `WORKFLOWS.md` for common patterns
4. **Follow checklists** - Instruction templates include checklists for completeness
5. **No restart needed** - Changes to `.cursor/rules/` are automatically detected

## Next Steps

1. Review `MIGRATION_GUIDE.md` for complete details
2. Test workflows with AI assistant
3. Customize instruction templates as needed
4. Share with team members

## See Also

- `.cursor/rules/constitution.md` - Project constitution (auto-reloaded, no restart needed)
- `.claude/` - Original Claude Desktop artifacts (kept for reference)

## Important Notes

- **`.cursor/rules/` is recommended** - Files here auto-reload without restarting Cursor
- **`.cursorrules` is deprecated** - Still works, but `.cursor/rules/` is preferred
- **Changes are detected automatically** - No need to restart Cursor when updating rules

