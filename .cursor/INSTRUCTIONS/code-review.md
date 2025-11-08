# Code Review Instructions

You are performing a comprehensive code review. Follow these steps:

## 1. Git Analysis

First, analyze the git changes:
- Identify current branch: `git branch --show-current`
- List changed files: `git diff --stat main...HEAD`
- Show detailed changes: `git diff main...HEAD`
- Review commits: `git log main..HEAD --oneline`

## 2. Code Quality Assessment

Analyze all changed files for:

### Python Code Quality
- PEP 8 compliance and formatting
- Type hints completeness and correctness (Principle III)
- Function/class structure and organization
- Error handling patterns (Principle II - Fail Fast)
- Code complexity and maintainability (Principle I - Radical Simplicity)
- Performance considerations

### Framework-Specific Patterns
- Handler/endpoint implementation structure
- Environment variable usage
- External service client initialization
- Error response formatting
- Resource management

## 3. Security Review

Check for:
- Hardcoded credentials or API keys
- Input validation and sanitization
- SQL/NoSQL injection vulnerabilities
- Sensitive data in logs or error messages
- IAM permission configurations
- Encryption settings (at rest and in transit)
- Authentication and authorization mechanisms

## 4. Architecture Compliance

Verify:
- Adherence to project patterns and conventions
- Service layer structure and dependency injection (Principle VI)
- Best practices (retry logic, timeouts, error handling)
- Infrastructure as Code quality (if applicable)
- Integration with existing systems
- Backwards compatibility

## 5. Testing Assessment

Evaluate:
- Unit test coverage for new/modified code
- Integration test adequacy
- Test quality and assertions
- Mock usage and test fixtures (Principle V)
- Error condition and edge case testing
- Test documentation
- Type hints in test code (Principle III)

## 6. Documentation Review

Check:
- Code comments and docstrings
- README.md or documentation updates needed
- API documentation (if applicable)
- Inline comments for complex logic
- Migration guides (if breaking changes)

## 7. Constitutional Compliance

Verify adherence to all 7 principles:
- **I. Radical Simplicity**: Simplest solution, functions <10 complexity, <50 statements
- **II. Fail Fast**: No defensive programming, no blind exception catching
- **III. Type Safety**: Type hints everywhere (including tests)
- **IV. Structured Data**: Pydantic/dataclasses, never loose dicts
- **V. Testing**: Appropriate mocking strategies
- **VI. Dependency Injection**: All dependencies REQUIRED (no Optional, no defaults), never created in constructors
- **VII. SOLID**: All five principles applied

## Output Format

Provide a structured review report with:

### Executive Summary
- Branch name and files changed count
- Overall recommendation: **Approve** / **Request Changes** / **Needs Discussion**
- Critical issues requiring immediate attention

### Detailed Findings

#### 🔍 Code Quality
- Style and formatting issues
- Type hints and documentation
- Structure and organization improvements
- Complexity violations (>10 cyclomatic complexity, >50 statements)

#### 🔒 Security Review
- Vulnerabilities identified
- Authentication/authorization concerns
- Data handling issues

#### 🏗️ Architecture Compliance
- Pattern adherence
- Best practices compliance
- Infrastructure quality
- Dependency injection violations

#### 🧪 Testing Assessment
- Coverage analysis
- Test quality evaluation
- Missing test scenarios
- Mock usage appropriateness

#### 📚 Documentation
- Documentation completeness
- Updates needed

#### ⚖️ Constitutional Compliance
- Principle violations identified
- Specific violations with file:line references
- Required fixes

### Actionable Recommendations

1. **🚨 Critical** (Must fix before merge)
2. **⚠️ Important** (Should address)
3. **💡 Suggestions** (Consider for future)
4. **✅ Positive Highlights** (Good practices observed)

### Pre-Merge Checklist
- [ ] All critical issues resolved
- [ ] Security vulnerabilities addressed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes without handling
- [ ] Code style compliant
- [ ] All constitutional principles followed
- [ ] Linting passes with zero violations

Be thorough, constructive, and provide specific examples with file paths and line numbers where applicable.

