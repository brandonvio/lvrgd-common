# Commit Instructions

Stage all changes, validate code quality, generate a meaningful commit message following repository conventions, create the commit, and push to remote.

## Process

### 1. Stage All Changes
```bash
git add .
```

### 2. Analyze Changes
- Review all staged changes: `git diff --cached`
- Identify files modified, added, deleted
- Understand the scope and nature of changes
- Note any breaking changes or significant features

### 3. Validate Code Quality

Before committing, ensure:
- Code follows `.cursorrules` (constitutional principles)
- Type hints are complete (Principle III)
- Linting passes: `ruff check` (zero violations)
- Code is formatted: `ruff format`
- Tests pass (if applicable)

### 4. Generate Commit Message

Generate a conventional commit message following these patterns:

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add email validation to user registration
fix(redis): resolve connection timeout issue
docs(readme): update installation instructions
refactor(services): simplify document processing logic
test(mongodb): add unit tests for query builder
```

**Body** (if needed):
- Explain what and why (not how)
- Reference issues or tickets if applicable
- Note breaking changes if any

### 5. Create Commit
```bash
git commit -m "<generated message>"
```

### 6. Push to Remote
```bash
git push
```

## Quality Gates

**DO NOT commit if**:
- Linting violations exist (`ruff check` must pass)
- Type hints are missing (Principle III violation)
- Tests are failing
- Constitutional principles are violated

**Always verify**:
- Commit message accurately describes changes
- No sensitive data in commit
- No large binary files accidentally included
- Branch is up to date with remote

## Example Execution

**Staged Changes**:
- Modified: `src/services/auth_service.py`
- Added: `tests/test_auth_service.py`
- Modified: `README.md`

**Generated Commit Message**:
```
feat(auth): add email validation to user registration

Add EmailValidator service with validation logic.
Update UserService to use EmailValidator via dependency injection.
Add comprehensive unit tests with appropriate mocking.
```

**Commands**:
```bash
git add .
git commit -m "feat(auth): add email validation to user registration

Add EmailValidator service with validation logic.
Update UserService to use EmailValidator via dependency injection.
Add comprehensive unit tests with appropriate mocking."
git push
```

## Notes

- Keep commit messages concise but descriptive
- One logical change per commit
- Use present tense ("add" not "added")
- Reference related issues: `Closes #123`
- For breaking changes: `BREAKING CHANGE: <description>`

