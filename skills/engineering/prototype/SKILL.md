---
name: prototype
description: Build a throwaway logic, UI, or feasibility prototype to answer one design question. Use when a runnable experiment will resolve uncertainty faster than discussion.
---

# Prototype

State the single question and the evidence that will answer it.

- For logic or feasibility, work under
  `.scratch/<prototype-slug>/` by default and follow [LOGIC.md](LOGIC.md).
- For UI, follow [UI.md](UI.md). Use a clearly marked temporary project route
  only when the question cannot be answered outside the application's routing
  environment.

Use only runtimes, libraries, and task runners already available in the target
project. Keep one command to run, no persistence unless persistence is the
question, and only enough error handling or styling to obtain reliable evidence.
Make relevant state visible after every interaction.

Finish with the question, result, run command, artifact paths, and the decision
the evidence supports. Keep the learning; do not promote prototype code to
production. Do not delete prototype files, create a branch, commit, or mutate an
issue tracker without the human's direction.
