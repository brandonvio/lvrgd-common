# Common Development Workflows

This document describes common development workflows adapted from Claude Desktop commands for use in Cursor.

## How to Use These Workflows

1. **Reference the workflow**: `@.cursor/WORKFLOWS.md`
2. **Copy the prompt**: Use the provided prompts in your conversations
3. **Follow the steps**: Execute the workflow as documented
4. **Reference instructions**: Use `@.cursor/INSTRUCTIONS/[workflow-name].md` for detailed instructions

---

## Code Review Workflow

**Purpose**: Perform comprehensive code review of git branch changes

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md

Review all changes in the current branch compared to main. Check for:
- Code quality and style compliance
- Type hints completeness
- Security vulnerabilities
- Architecture compliance
- Test coverage
- Documentation
```

**Steps**:
1. **Git Analysis**
   ```bash
   git branch --show-current
   git diff --stat main...HEAD
   git diff main...HEAD
   git log main..HEAD --oneline
   ```

2. **AI Review** - Use the prompt above

3. **Review Checklist**
   - [ ] All critical issues resolved
   - [ ] Security vulnerabilities addressed
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes without handling
   - [ ] Code style compliant

---

## Commit Workflow

**Purpose**: Stage changes, validate code quality, generate commit message, and push

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/commit.md

Stage all changes, analyze them, generate a meaningful conventional commit message,
create the commit, and push to remote.
```

**Steps**:
1. **Stage Changes** (AI will do this)
2. **AI Generates Commit** - Use the prompt above
3. **Verify**
   - Check commit message accuracy
   - Confirm push succeeded

---

## Work Command Workflow

**Purpose**: Implement features with strict constitutional compliance and task tracking

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-execution.md

Implement [feature description] following all constitutional principles.
Break down into tasks, track progress, and ensure compliance.
```

**What AI Will Do**:
- Load and follow `.cursor/rules/constitution.md` (constitution)
- Break down into discrete tasks
- Track progress with todo list
- Ensure all 7 principles are followed
- Run linting and tests before completion

**Example**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-execution.md

Implement user authentication service with email validation.
Break down into tasks, track progress, and ensure constitutional compliance.
```

---

## Generate Specification Workflow

**Purpose**: Create comprehensive technical specification from prompt or requirements

**Prompt** (from file):
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/spec-generation.md

Generate a comprehensive technical specification from @specs/[feature-name]-prompt.md
Follow the standardized 15-section format.
Save as specs/[feature-name]-spec.md
```

**Prompt** (direct):
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/spec-generation.md

Generate a comprehensive technical specification for: [feature description]

Analyze the codebase systematically:
- Identify affected components and integration points
- Determine file structure and naming conventions
- Map dependencies and architecture patterns
- Review existing similar features for consistency

Follow the standardized 15-section specification format.
Save to specs/[feature-name]-spec.md using kebab-case naming.
```

**Steps**:
1. Create prompt file (optional): `specs/[feature-name]-prompt.md`
2. Use appropriate prompt above
3. Review and refine generated spec
4. Use spec as implementation guide

---

## Generate Tasks Workflow

**Purpose**: Generate constitution-compliant task breakdown from specification

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-generation.md

Generate a comprehensive task breakdown for the specification file: @specs/[feature-name]-spec.md

Read the project constitution at @.cursor/rules/constitution.md and ensure all tasks comply with:
- Radical Simplicity
- Fail Fast Philosophy
- Comprehensive Type Safety
- Structured Data Models
- Unit Testing with Mocking
- Dependency Injection
- SOLID Principles

Save the tasks file as: specs/[feature-name]-tasks.md
```

**Steps**:
1. Ensure spec file exists: `specs/[feature-name]-spec.md`
2. Use prompt above
3. Review generated tasks
4. Execute tasks: See "Execute Tasks Workflow"

---

## Execute Tasks Workflow

**Purpose**: Execute tasks from tasks.md file with automated constitutional compliance and review-refine loop

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/task-execution.md @.cursor/INSTRUCTIONS/code-review.md

Execute ALL tasks from @specs/[feature-name]-tasks.md (or @specs/[feature-name]-r{N}-tasks.md)

PRIMARY MANDATE: Execute ALL tasks from start to finish WITHOUT stopping.

1. Read @.cursor/rules/constitution.md
2. Load tasks from the tasks file
3. Execute ALL tasks sequentially (NO STOPPING, NO CONFIRMATION)
4. Update EVERY checkbox IMMEDIATELY after completion
5. Apply all 7 constitutional principles

After implementation, perform constitutional code review:
1. Read @.cursor/rules/constitution.md
2. Read specification file (derive from tasks file path)
3. Read tasks file
4. Identify all implemented files
5. Audit EVERY file against 7 constitutional principles
6. Verify ALL requirements implemented
7. Validate ALL checkboxes addressed
8. Generate output:
   - If issues found: Create specs/[basename]-r{N}-tasks.md
   - If approved: Create specs/[basename]-r{N}-approval.md

If refinement tasks are generated, loop back and execute them.
Continue until approval is granted or maximum iterations reached.
```

**Iteration Pattern**:
- **Initial**: `specs/feature-tasks.md`
- **Refinement 1**: `specs/feature-r1-tasks.md`
- **Refinement 2**: `specs/feature-r2-tasks.md`
- **Approval**: `specs/feature-r{N}-approval.md`

**Steps**:
1. Ensure tasks file exists
2. Use prompt above
3. AI will execute tasks and review
4. If issues found, AI generates refinement tasks
5. Loop continues until approval

---

## Pythonic Refactor Workflow

**Purpose**: Refactor code to be more Pythonic and idiomatic

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/pythonic-refactor.md

Refactor [file/function/class] to be more Pythonic and idiomatic while maintaining
all constitutional principles.
```

---

## Format Markdown Workflow

**Purpose**: Format markdown files consistently

**Prompt**:
```
Format the markdown file: [file-path]
Ensure consistent formatting, proper heading hierarchy, and readability.
```

---

## Generate README Workflow

**Purpose**: Generate or update README.md for project or module

**Prompt**:
```
@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/readme-generation.md

Generate/update README.md for [project/module].
Include:
- Overview and purpose
- Installation instructions
- Usage examples
- API documentation
- Development guidelines
```

---

## Generate Merge Request Documentation

**Purpose**: Generate documentation for merge requests

**Prompt**:
```
@.cursor/rules/constitution.md

Generate merge request documentation for the current branch changes.
Include:
- Summary of changes
- Files modified/added/deleted
- Testing performed
- Breaking changes (if any)
- Migration notes (if needed)
```

---

## Quick Reference

| Workflow | Instruction File | Key Prompt |
|----------|-----------------|------------|
| Code Review | `code-review.md` | Review changes in current branch |
| Commit | `commit.md` | Stage, commit, and push changes |
| Work | `task-execution.md` | Implement feature with compliance |
| Generate Spec | `spec-generation.md` | Create technical specification |
| Generate Tasks | `task-generation.md` | Create task breakdown from spec |
| Execute Tasks | `task-execution.md` + `code-review.md` | Execute tasks with review loop |
| Refactor | `pythonic-refactor.md` | Refactor to be more Pythonic |

---

## Tips

1. **Always reference constitution** - Include `@.cursor/rules/constitution.md` in important conversations
2. **Combine instructions** - You can reference multiple files: `@.cursor/rules/constitution.md @.cursor/INSTRUCTIONS/code-review.md`
3. **Use specific prompts** - Copy the exact prompts from this document
4. **Follow checklists** - Use the provided checklists to ensure completeness
5. **Iterate as needed** - Workflows can be repeated until satisfaction
6. **No restart needed** - Changes to `.cursor/rules/` are automatically detected

---

## See Also

- `.cursor/rules/constitution.md` - Project constitution (auto-reloaded)
- `.cursor/INSTRUCTIONS/` - Detailed instruction templates
- `.cursor/TOOL_PERMISSIONS.md` - Allowed tools and operations
- `.cursor/MIGRATION_GUIDE.md` - Migration guide from Claude Desktop

