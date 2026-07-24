---
name: tdd
description: Apply red-green test-driven development to observable behavior through a public seam. Use for feature work, bug fixes, integration tests, or explicit red-green requests.
---

# Test-Driven Development

Before editing, state whether the task changes observable behavior.

- If the change is testable through a public seam, use red-green TDD.
- Otherwise, explain in one sentence why TDD does not apply and name the
  alternative verification.

A clear existing seam does not require interrupting the human. Ask only when
materially different seam choices would change architecture or testing cost.
Do not install a test framework into a project that lacks one.

## Red-green loop

1. Write one behavior test through the public interface.
2. Run it and preserve evidence that it fails for the expected reason.
3. Make the smallest production change that satisfies that behavior.
4. Run the narrow test and preserve green evidence.
5. Repeat with the next complete behavior slice.

Tests describe what callers observe and survive internal refactors. Avoid
private-method assertions, internal collaborator mocks, call-count assertions,
tautological expected values, and bulk horizontal test writing. Mock only true
system boundaries; see [tests.md](tests.md) and [mocking.md](mocking.md).

Completion requires the red and green commands/results for each slice plus the
applicable broader project checks, or evidence from the declared alternative
verification.
