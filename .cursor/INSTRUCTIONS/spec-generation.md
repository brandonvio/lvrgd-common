# Specification Generation Instructions

Generate a comprehensive, standardized technical specification document.

## Process

### 1. Analyze Requirements

If prompt file provided:
- Read the prompt file: `@specs/[feature-name]-prompt.md`
- Understand the requirements and goals

If direct input:
- Analyze the user's requirements
- Identify the feature scope and objectives

### 2. Codebase Analysis

Analyze the codebase systematically:
- Identify affected components and integration points
- Determine file structure and naming conventions
- Map dependencies and architecture patterns
- Review existing similar features for consistency
- Understand existing service patterns
- Check existing data models and structures

### 3. Generate Specification

Follow the standardized 15-section specification format:

1. **Overview** - Feature summary and purpose
2. **Requirements** - Functional and non-functional requirements
3. **Architecture** - System design and component structure
4. **Data Models** - Pydantic/dataclass models needed (Principle IV)
5. **Services** - Service layer design with dependency injection (Principle VI)
6. **API Design** - Endpoints, request/response models (if applicable)
7. **Integration Points** - External services, dependencies
8. **Error Handling** - Error types and handling strategy (Principle II - Fail Fast)
9. **Testing Strategy** - Unit tests, integration tests, mocking approach (Principle V)
10. **Performance Considerations** - Scalability, optimization needs
11. **Security** - Authentication, authorization, data protection
12. **Configuration** - Environment variables, settings
13. **Documentation** - Code comments, API docs, README updates
14. **Migration Plan** - Breaking changes, migration steps (if applicable)
15. **Constitutional Analysis** - How each principle applies

### 4. Constitutional Compliance

Ensure specification aligns with all 7 principles:

- **I. Radical Simplicity**: Simplest solution approach
- **II. Fail Fast**: No defensive programming, fail immediately
- **III. Type Safety**: Comprehensive type hints everywhere
- **IV. Structured Data**: Pydantic/dataclasses for all data structures
- **V. Testing**: Appropriate mocking strategies
- **VI. Dependency Injection**: All dependencies REQUIRED (no Optional, no defaults)
- **VII. SOLID**: All five principles in design

### 5. Save Specification

**File Naming**:
- From prompt file: `specs/[basename]-spec.md` (replace `-prompt.md` with `-spec.md`)
- From direct input: `specs/[feature-name]-spec.md` (kebab-case)

**Location**: `specs/` directory

## Output Format

```markdown
# Technical Specification: [Feature Name]

**Generated**: [date]
**Status**: Draft | Ready for Review

## 1. Overview
[Feature summary and purpose]

## 2. Requirements
### Functional Requirements
- [Requirement 1]
- [Requirement 2]

### Non-Functional Requirements
- [Performance, security, etc.]

## 3. Architecture
[System design and component structure]

## 4. Data Models
[Pydantic/dataclass models with type hints]

## 5. Services
[Service layer design with dependency injection]

## 6. API Design
[If applicable: endpoints, request/response models]

## 7. Integration Points
[External services, dependencies]

## 8. Error Handling
[Error types and fail-fast strategy]

## 9. Testing Strategy
[Unit tests, integration tests, mocking approach]

## 10. Performance Considerations
[Scalability, optimization]

## 11. Security
[Authentication, authorization, data protection]

## 12. Configuration
[Environment variables, settings]

## 13. Documentation
[Code comments, API docs, README updates]

## 14. Migration Plan
[Breaking changes, migration steps if applicable]

## 15. Constitutional Analysis
### Principle I: Radical Simplicity
[How simplest solution applies]

### Principle II: Fail Fast
[Fail-fast approach]

### Principle III: Type Safety
[Type hints strategy]

### Principle IV: Structured Data
[Pydantic/dataclass usage]

### Principle V: Testing
[Mocking strategies]

### Principle VI: Dependency Injection
[Dependency injection design - all REQUIRED]

### Principle VII: SOLID
[How SOLID principles apply]
```

## Quality Standards

- Comprehensive coverage of all aspects
- Clear, actionable requirements
- Constitutional compliance verified
- Consistent with existing codebase patterns
- Ready for task breakdown generation

## Next Steps

After generating specification:
1. Review for completeness
2. Address any open questions
3. Use as implementation guide
4. Generate tasks: See task-generation.md

