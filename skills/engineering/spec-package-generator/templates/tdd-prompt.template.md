---
artifactId: tdd-prompt
stage: final
status: template
version: 3
dependsOn:
  - task-execution-manifest.template.yaml
invalidates: []
summary: Minimal derived invocation for the formal spec Task executor.
keyDecisions: []
openQuestions: []
---

# Implement One Approved Task

`$implement-spec-task <manifest-path>`

Replace `<manifest-path>` with the selected Task's generated YAML Manifest.
The Manifest and referenced Task package own all execution inputs; this prompt
must not restate or override them.
