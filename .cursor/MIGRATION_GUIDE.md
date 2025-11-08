# Migration Guide: Claude Artifacts → Cursor

This guide explains how to adapt the `.claude` artifacts for use in Cursor.

## Overview

Cursor uses different mechanisms than Claude Desktop for configuration:
- **`.cursorrules`** - Project-wide rules and instructions (equivalent to constitution + agent instructions)
- **`.cursor/` directory** - Cursor-specific configurations
- **No slash commands** - Cursor doesn't support custom slash commands like Claude
- **No agent system** - Cursor uses a single AI assistant, not multiple agents

## Artifact Mapping

### 1. Constitution (`constitution.md`) → `.cursor/rules/constitution.md`

**Status**: ✅ Direct migration possible

The `constitution.md` file contains your core development principles. This should be placed in `.cursor/rules/constitution.md`.

**Action**: Copy `constitution.md` to `.cursor/rules/constitution.md`.

```bash
cp .claude/constitution.md .cursor/rules/constitution.md
```

**How it works in Cursor**:
- Cursor automatically reads `.cursor/rules/` directory (auto-reloads on changes)
- The AI assistant will follow these principles for all code generation and editing
- You can reference it in conversations: `@.cursor/rules/constitution.md`
- **No restart required** - changes are automatically detected

**Note**: `.cursorrules` is deprecated but still works. Using `.cursor/rules/` is the recommended approach for better auto-reload support.

---

### 2. Settings (`settings.json`, `settings.local.json`) → Documentation

**Status**: ⚠️ No direct equivalent, document as guidelines

Cursor doesn't have a permissions system like Claude Desktop. These settings define what tools/commands are allowed.

**Action**: Create `.cursor/TOOL_PERMISSIONS.md` documenting allowed operations:

```markdown
# Tool Permissions and Guidelines

## Allowed Operations

The AI assistant may use these tools/commands:

### Git Operations
- `git add`, `git commit`, `git push`, `git pull`
- `git branch`, `git checkout`, `git merge`

### Code Quality
- `ruff check`, `ruff format`
- `python3 -m pytest`, `uv run pytest`

### Development Tools
- `python`, `python3`, `uv`
- `gh` (GitHub CLI)
- `source` (for environment setup)

### File Operations
- `tree` (directory listing)

## Denied Operations

None currently - all operations are allowed.

## Usage Notes

- Always run `ruff format` before committing
- Always run `ruff check` and fix violations before marking code complete
- Run tests before committing changes
```

**How it works in Cursor**:
- The AI assistant will naturally use these tools when needed
- You can reference this document: `@.cursor/TOOL_PERMISSIONS.md`
- Consider adding reminders in `.cursorrules` about running linting/tests

---

### 3. Commands (`commands/*.md`) → Workflow Documentation

**Status**: ⚠️ Convert to documented workflows

Claude Desktop supports custom slash commands. Cursor doesn't, but you can:
1. Document workflows for manual execution
2. Create reusable prompts/templates
3. Reference them in conversations

**Action**: Create `.cursor/WORKFLOWS.md` documenting common workflows:

```markdown
# Common Development Workflows

## Code Review Workflow

To perform a comprehensive code review:

1. **Git Analysis**
   ```bash
   git branch --show-current
   git diff --stat main...HEAD
   git diff main...HEAD
   git log main..HEAD --oneline
   ```

2. **Ask AI to Review**
   ```
   Review all changes in the current branch compared to main. 
   Check for:
   - Code quality and style compliance
   - Type hints completeness
   - Security vulnerabilities
   - Architecture compliance
   - Test coverage
   - Documentation
   ```

3. **Follow Review Checklist**
   - [ ] All critical issues resolved
   - [ ] Security vulnerabilities addressed
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes without handling
   - [ ] Code style compliant

## Commit Workflow

To commit changes with auto-generated message:

1. **Stage Changes**
   ```bash
   git add .
   ```

2. **Ask AI to Generate Commit**
   ```
   Analyze all staged changes and generate a conventional commit message.
   Then create the commit and push to remote.
   ```

3. **Verify**
   - Check commit message accuracy
   - Confirm push succeeded

## Work Command Workflow

To implement features with constitutional compliance:

1. **Provide Instructions**
   ```
   Implement [feature description] following all constitutional principles.
   Break down into tasks, track progress, and ensure compliance.
   ```

2. **AI Will**:
   - Load and follow `.cursorrules` (constitution)
   - Break down into discrete tasks
   - Track progress with todo list
   - Ensure all principles are followed
   - Run linting and tests before completion

## Generate Spec Workflow

To create a technical specification:

1. **Create Prompt File** (optional)
   ```
   specs/[feature-name]-prompt.md
   ```

2. **Ask AI**
   ```
   Generate a comprehensive technical specification from @specs/[feature-name]-prompt.md
   Follow the standardized 15-section format.
   Save as specs/[feature-name]-spec.md
   ```

3. **Review and Refine**
   - Review generated spec
   - Address open questions
   - Use as implementation guide

[Add other workflows from commands/ directory]
```

**How it works in Cursor**:
- Reference workflows: `@.cursor/WORKFLOWS.md`
- Copy/paste workflow prompts into conversations
- AI will follow the documented process

---

### 4. Agents (`agents/*.md`) → Specialized Instructions

**Status**: ⚠️ Convert to reusable instruction templates

Claude Desktop has multiple specialized agents. Cursor has one AI assistant, but you can create instruction templates for different scenarios.

**Action**: Create `.cursor/INSTRUCTIONS/` directory with specialized instruction files:

```
.cursor/
  INSTRUCTIONS/
    code-review.md          # Instructions for code reviews
    commit.md               # Instructions for commits
    spec-generation.md      # Instructions for spec generation
    task-execution.md       # Instructions for task execution
    refactoring.md          # Instructions for refactoring
    ...
```

**Example**: `.cursor/INSTRUCTIONS/code-review.md`

```markdown
# Code Review Instructions

You are performing a comprehensive code review. Follow these steps:

1. **Git Analysis**
   - Identify current branch: `git branch --show-current`
   - List changed files: `git diff --stat main...HEAD`
   - Show detailed changes: `git diff main...HEAD`
   - Review commits: `git log main..HEAD --oneline`

2. **Code Quality Assessment**
   - PEP 8 compliance and formatting
   - Type hints completeness
   - Function/class structure
   - Error handling patterns
   - Code complexity
   - Performance considerations

3. **Security Review**
   - Hardcoded credentials
   - Input validation
   - SQL injection vulnerabilities
   - Sensitive data in logs
   - Authentication/authorization

4. **Architecture Compliance**
   - Adherence to project patterns
   - Service layer structure
   - Dependency injection
   - Best practices

5. **Testing Assessment**
   - Unit test coverage
   - Integration test adequacy
   - Test quality
   - Mock usage

6. **Documentation Review**
   - Code comments and docstrings
   - README updates needed
   - API documentation

Provide structured review report with:
- Executive Summary
- Detailed Findings (Code Quality, Security, Architecture, Testing, Documentation)
- Actionable Recommendations (Critical, Important, Suggestions, Positive Highlights)
- Pre-Merge Checklist
```

**How it works in Cursor**:
- Reference instructions: `@.cursor/INSTRUCTIONS/code-review.md`
- AI will follow the specialized instructions
- Combine with `.cursorrules` for full context

---

## Recommended Cursor Structure

```
project-root/
├── .cursor/
│   ├── rules/                      # Project rules (auto-reloaded)
│   │   └── constitution.md        # Constitution (from .claude/constitution.md)
│   ├── TOOL_PERMISSIONS.md         # Allowed tools/commands
│   ├── WORKFLOWS.md                # Common workflows
│   └── INSTRUCTIONS/               # Specialized instruction templates
│       ├── code-review.md
│       ├── commit.md
│       ├── spec-generation.md
│       ├── task-execution.md
│       ├── refactoring.md
│       └── ...
└── .claude/                        # Keep original (for reference)
    ├── constitution.md
    ├── settings.json
    ├── commands/
    └── agents/
```

**Note**: `.cursor/rules/` is the recommended location. Files here are automatically reloaded without restarting Cursor.

---

## Usage Examples

### Example 1: Code Review

```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md

Review all changes in the current branch compared to main.
```

### Example 2: Implementing a Feature

```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-execution.md

Implement user authentication service with email validation.
Break down into tasks, track progress, and ensure constitutional compliance.
```

### Example 3: Generating a Spec

```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/spec-generation.md

Generate a technical specification from @specs/websocket-prompt.md
```

### Example 4: Committing Changes

```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/commit.md

Stage all changes, analyze them, generate a conventional commit message,
create the commit, and push to remote.
```

---

## Key Differences

| Claude Desktop | Cursor |
|----------------|--------|
| Slash commands (`/work`, `/commit`) | Manual prompts with instruction files |
| Multiple specialized agents | Single AI assistant with instruction templates |
| `settings.json` permissions | Documented in `TOOL_PERMISSIONS.md` |
| `constitution.md` | `.cursor/rules/constitution.md` (recommended) or `.cursorrules` (deprecated) |
| Agent definitions | Instruction templates in `INSTRUCTIONS/` |

---

## Migration Checklist

- [x] Copy `constitution.md` → `.cursor/rules/constitution.md`
- [x] Create `.cursor/TOOL_PERMISSIONS.md` from `settings.json`
- [x] Create `.cursor/WORKFLOWS.md` from `commands/*.md`
- [x] Create `.cursor/INSTRUCTIONS/` directory
- [x] Convert each agent file to instruction template
- [ ] Test workflows with AI assistant
- [ ] Update team documentation
- [ ] Keep `.claude/` directory for reference

**Note**: `.cursor/rules/` files auto-reload without restarting Cursor. `.cursorrules` is deprecated but still works.

---

## Tips for Effective Use

1. **Always reference constitution** - Include `@.cursor/rules/constitution.md` in important conversations
2. **Use instruction templates** - Reference specific instructions for specialized tasks
3. **Combine multiple references** - You can reference multiple files: `@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md`
4. **Create custom instructions** - Add project-specific instruction templates as needed
5. **Document workflows** - Keep `.cursor/WORKFLOWS.md` updated with common patterns
6. **No restart needed** - Changes to `.cursor/rules/` are automatically detected

---

## Next Steps

1. Review this migration guide
2. Execute the migration checklist
3. Test workflows with the AI assistant
4. Refine instruction templates based on usage
5. Share with team members

