# Project Rules

## Workflow & Verification
- **Test After Every Step**: After completing each step requested by the user, run the app/tests yourself to verify it actually works as intended (no errors, expected behavior confirmed).
- **Verification Summary**: Once verified, stop and show a summary of what was done and ask the user to review it.
- **Git Commit Protocol**:
  - Do not run git commit yourself — wait for explicit confirmation from the user.
  - Once the user confirms it's working and approves, create a git commit with a clear, descriptive commit message summarizing that step.
  - Do not proceed to the next step until the commit is made and confirmed by the user.
