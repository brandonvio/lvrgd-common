# Task Generation Instructions

Generate a comprehensive, constitution-compliant task breakdown from a specification file.

## Process

### 1. Read Specification

Read the specification file:
- Parse constitutional spec to understand requirements
- Identify component breakdown (models, services, integration points)
- Note testing requirements
- Understand implementation approach

**Note**: Spec should already be analyzed against constitution. Focus on task breakdown, not re-analyzing compliance.

### 2. Break Down into Tasks

Transform specification into discrete, actionable tasks:

**Task Sequencing** (Build in Order):
1. **Data Models First** (Principle IV) - Pydantic/dataclass definitions
2. **Service Layer Second** (Principles VI, VII) - Business logic with dependency injection
3. **Integration Third** (Principle V) - External service integrations
4. **Testing Fourth** (Principle V) - Unit tests with appropriate mocking
5. **Quality Gates Last** - Linting, formatting, final validation

### 3. Task Structure

Each task includes:
- **Clear description**: What needs to be implemented
- **Constitutional principles**: Which principles apply (I, II, III, etc.)
- **Implementation notes**: High-level guidance (not code examples)
- **Files involved**: What to create/modify
- **Dependencies**: What must be done first

### 4. Generate Task File

**File Naming**:
- Pattern: `{spec-filename-without-extension}-tasks.md`
- Example: `specs/feature-spec.md` → `specs/feature-spec-tasks.md`
- Location: Same directory as specification file

## Output Format

```markdown
# Task Breakdown: [Feature Name]

**Generated**: [date]
**Source Spec**: `specs/[name]-spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [ ] 1. Create [ModelName] Pydantic model
- [ ] 2. Implement [ServiceName] with dependency injection
- [ ] 3. Add [integration/feature]
- [ ] 4. Write unit tests with appropriate mocking
- [ ] 5. Run linting and formatting
- [ ] 6. Verify all constitutional requirements met

---

## Specification Summary

[Brief 2-3 sentence summary of what needs to be implemented]

---

## Detailed Task Implementation Guidance

### Task 1: Create [ModelName] Pydantic Model
- **Constitutional Principles**: IV (Structured Data), III (Type Safety)
- **Implementation Approach**:
  - Define Pydantic BaseModel with typed fields
  - Include field descriptions
  - Keep it simple - data definition only, no business logic
- **Files to Create**: `[path/to/model.py]`
- **Dependencies**: None

### Task 2: Implement [ServiceName] with Dependency Injection
- **Constitutional Principles**: VI (Dependency Injection), VII (SOLID), I (Simplicity)
- **Implementation Approach**:
  - Constructor injection pattern
  - ALL dependencies REQUIRED (no Optional, no defaults)
  - Single responsibility (Principle VII)
  - Fail fast - no fallback logic (Principle II)
- **Files to Create**: `[path/to/service.py]`
- **Dependencies**: Task 1 (needs model)

[Continue for all tasks...]

---

## Constitutional Principle Reference

- **I** - Radical Simplicity
- **II** - Fail Fast Philosophy
- **III** - Comprehensive Type Safety
- **IV** - Structured Data Models
- **V** - Unit Testing with Mocking
- **VI** - Dependency Injection (all REQUIRED)
- **VII** - SOLID Principles

---

## Success Criteria

### Functional Requirements (from spec)
- [ ] [Functional requirement 1]
- [ ] [Functional requirement 2]

### Constitutional Compliance
- [ ] All code follows radical simplicity (I)
- [ ] Fail fast applied throughout (II)
- [ ] Type hints on all functions (III)
- [ ] Pydantic/dataclass models used (IV)
- [ ] Unit tests use appropriate mocking (V)
- [ ] Dependency injection implemented (VI) - all REQUIRED
- [ ] SOLID principles maintained (VII)

### Code Quality Gates
- [ ] All functions have type hints
- [ ] All services use constructor injection
- [ ] No defensive programming unless requested
- [ ] Models are simple data definitions
- [ ] Tests use appropriate mocking
- [ ] Code formatted with ruff
- [ ] Linting passes (zero violations)
```

## Quality Standards

### Task Clarity
- Tasks must be specific and actionable
- Clear acceptance criteria
- Concrete but high-level guidance (not code examples)
- Proper sequencing with dependencies

### Lean Approach
- Focus on WHAT to implement
- Reference principles (I-VII) by number
- Let executor determine HOW to implement
- No redundant constitutional examples (executor has those)
- Keep guidance concise

## Notes

- Tasks feed directly into task executor
- Executor reads `.cursor/rules/constitution.md` for detailed guidance
- Executor has code examples and implementation patterns
- No need to duplicate constitutional guidance here
- Focus on task breakdown and sequencing

## Next Steps

After generating tasks:
1. Review task breakdown
2. Execute tasks using task-execution.md instructions
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time

