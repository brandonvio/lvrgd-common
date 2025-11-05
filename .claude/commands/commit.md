---
title: commit
description: Stage all changes and commit with auto-generated message
---

Analyze all staged and unstaged changes, generate a concise commit message following repository conventions, then commit all changes.

Steps:
Validation!
1. Run `flake8` and resovle all linting errors.
2. For each Python file modified in branch... run `black` on that file.
3. Do not proceed until validation successfully passes.

Commit!
1. Run `git status` to see all changes
2. Run `git diff` to analyze the changes
3. Run `git log --oneline -5` to understand commit message style
4. Stage all changes with `git add -A`. Ensure to run `git add -A` before proceeding.
5. Generate a commit message that:
   - Summarizes the main change in the first line (50 chars or less)
   - Uses imperative mood (e.g., "Add", "Fix", "Update")
   - Follows the repository's commit conventions, but error on the verbose side to have meaningful commit messages.
6. Commit with the generated message
7. Show the commit status to confirm success
8. Run `git push` to push the commits to the remote server.

Always include the Claude Code signature at the end of the commit message.