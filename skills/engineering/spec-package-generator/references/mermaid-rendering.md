# Mermaid rendering

Mermaid `.mmd` files are the authoritative diagram sources:

- Gate 1: `diagrams/user-flow.mmd`
- Gate 2: `diagrams/api-flow.mmd`
- Multi-project Gate 2: `diagrams/cross-project-flow.mmd`

Gate 1 diagrams remain business-level. Gate 2 nodes must trace to a verified,
confirmed-design, or explicitly accepted `UNVERIFIED` context entry.

## Optional SVG rendering

SVG files are reproducible review artifacts. Use the official
`@mermaid-js/mermaid-cli` package through `mmdc`. MySkills centrally owns its
version and installation. Do not install a renderer from inside this Skill.

When `mmdc` is available:

1. write the `.mmd` source first;
2. validate and render the adjacent `.svg`;
3. link both files from the gate review artifact;
4. retain the `.mmd` and record the rendering error if SVG generation fails.

When `mmdc` is unavailable, continue with the complete `.mmd`-only workflow and
record:

```text
SVG rendering was skipped because the optional Mermaid CLI was unavailable.
The Mermaid .mmd source remains authoritative and can be rendered later.
```

Absence of optional SVG rendering never blocks a gate or makes the specification
package incomplete.

At each review gate, present the review artifact path, `.mmd` path, optional SVG
path, a concise diagram summary, and the exact confirmation requested.
