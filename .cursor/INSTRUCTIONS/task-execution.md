# Task Execution Instructions

Execute work based on user instructions while strictly adhering to constitutional principles with comprehensive task tracking.

## Core Mandate

**EXECUTE ALL TASKS TO COMPLETION**: Implement ALL tasks sequentially from start to finish WITHOUT stopping for user confirmation. Work autonomously through the entire task list.

**REAL-TIME UPDATES**: Update task checkboxes IMMEDIATELY after completing each individual task. Never wait to batch updates.

## Initialization

### 1. Load Constitutional Principles

Read and internalize `.cursor/rules/constitution.md` to ensure compliance with all 7 NON-NEGOTIABLE principles:

- **I. Radical Simplicity** - Simplest solution, functions <10 complexity, <50 statements
- **II. Fail Fast** - No defensive programming, no blind exception catching
- **III. Type Safety** - Type hints EVERYWHERE (including tests)
- **IV. Structured Data** - Pydantic/dataclasses, never loose dicts
- **V. Unit Testing** - Appropriate mocking strategies
- **VI. Dependency Injection** - All dependencies REQUIRED (no Optional, no defaults), NEVER created in constructors
- **VII. SOLID** - All five principles strictly applied

### 2. Break Down Instructions

Analyze user instructions and create a comprehensive task breakdown:
- Each task should be specific and measurable
- Include file paths where applicable
- Note which constitutional principles apply
- Identify dependencies between tasks
- Estimate complexity (simple/moderate/complex)

### 3. Initialize Task Tracking

Create a todo list for progress tracking using TodoWrite:
- Mark tasks as "pending" initially
- Update status to "in_progress" when starting
- Mark as "completed" when finished
- Mark as "failed" if errors occur

## Task Execution Workflow

### For EACH Task:

#### 1. Mark Task In Progress
Update TodoWrite: status = "in_progress"

#### 2. Constitutional Compliance Check
Before implementing, verify:
- **Principle I**: Is this the simplest approach?
- **Principle II**: No defensive programming, let it fail if assumptions violated
- **Principle III**: All functions will have type hints
- **Principle IV**: Using Pydantic/dataclass, not dicts
- **Principle VI**: All dependencies REQUIRED (no Optional, no defaults), NEVER create in constructors
- **Principle VII**: All five SOLID principles maintained

#### 3. Implementation
Execute the task autonomously:
- Write the simplest code that works (Principle I)
- Add type hints to ALL parameters and return values (Principle III)
- Use Pydantic models or dataclasses for structured data (Principle IV)
- Implement dependency injection - all dependencies REQUIRED, no Optional, no defaults, NEVER create inside constructors (Principle VI)
- Follow SOLID principles rigorously (Principle VII)
- Let systems fail fast - no fallback logic (Principle II)
- Follow existing project conventions and patterns

#### 4. Linting Quality Gate (MANDATORY)
BEFORE marking complete:
1. Run: `ruff format {modified_files}`
2. Run: `ruff check --fix {modified_files}`
3. Run: `ruff check {modified_files}`
4. If violations exist: STOP and manually resolve:
   - C901/PLR0915 (complexity >10 or >50 statements) → refactor into smaller functions (VIOLATES Principle I)
   - BLE001 (blind exception) → use specific exception types (VIOLATES Principle II)
   - A002 (builtin shadow) → rename variables
   - PERF* (performance) → apply optimizations
   - FBT* (boolean args) → use named parameters or enums
   - SIM* (simplification) → apply suggested pattern
5. Re-run: `ruff check {modified_files}`
6. Only proceed when `ruff check` reports ZERO violations

#### 5. Update Task Status
Update TodoWrite: status = "completed"

## Completion Summary

After all tasks are complete, provide:

### Summary Report
- Original instructions
- Tasks completed: X/Y
- Files modified/created (with absolute paths)
- Constitutional compliance confirmation
- Key changes made
- Next steps recommendations

### Constitutional Compliance Checklist
- [ ] Radical Simplicity - Implemented simplest solution (functions <10 complexity, <50 statements)
- [ ] Fail Fast - No defensive programming, no blind exception catching
- [ ] Type Safety - Type hints on ALL functions and parameters
- [ ] Structured Data - Used Pydantic/dataclasses, not dicts
- [ ] Unit Testing - Added tests with appropriate mocking
- [ ] Dependency Injection - All deps REQUIRED, none created in constructors
- [ ] SOLID Principles - SRP, OCP, LSP, ISP, DIP all followed
- [ ] Linting Clean - Zero violations from `ruff check` (MANDATORY)

## Error Handling

If error occurs during task execution:
1. Mark current task as "failed" in TodoWrite
2. Display error details clearly
3. Provide context about what was being attempted
4. Suggest resolution steps if possible
5. Continue with remaining tasks OR stop if critical failure
6. Include failure summary in completion report

## Autonomous Operation

- **DO NOT** ask "Should I continue?"
- **DO NOT** ask "Is this approach okay?"
- **DO NOT** wait for confirmation between tasks
- **JUST KEEP IMPLEMENTING** according to constitutional principles
- Make implementation decisions based on constitutional principles
- Work through entire task list without user intervention

## Key Reminders

1. Read `.cursor/rules/constitution.md` BEFORE starting
2. Break down instructions into discrete tasks
3. Track progress with TodoWrite
4. Update checkboxes in real-time
5. Apply all 7 constitutional principles
6. Run linting before marking complete
7. Work autonomously - no confirmation needed
8. Complete entire task list

