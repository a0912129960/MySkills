# UI prototype

Build several visibly different variants that answer one presentation or
interaction question. The human should be able to compare them in one run.

## Choose the lightest environment

Start under `.scratch/<prototype-slug>/` with the target project's existing
runtime, components, styles, and fixtures. Prefer a standalone local page when
it can answer the question honestly.

Use a clearly named temporary route in the application only when the question
depends on real routing, layout, authentication, data density, or framework
behavior that cannot be reproduced outside it. Preserve the project's routing
conventions and isolate all prototype changes so they are easy to identify.

## Build variants

Create at least three meaningfully different directions. Changing only colors,
spacing, or labels does not create a distinct direction.

Expose all variants through one obvious switcher. In a routed prototype, a
`?variant=` query parameter is useful because comparisons remain reloadable and
shareable. Show the current variant and the relevant UI state.

Use realistic density and representative content. Reuse existing UI
dependencies; do not add a repository-wide package for the experiment. Skip
production hardening, exhaustive error handling, broad accessibility work, and
tests unless one of them is the design question.

## Conclude

Report:

- the original question;
- the run command and artifact or route;
- the variants compared;
- the observed winner, rejected directions, and why;
- the production decision the evidence supports.

Do not silently turn the winner into production code. Keep all prototype files
until the human directs promotion, retention, or deletion. Do not create a
branch, commit, or issue as part of this workflow.
