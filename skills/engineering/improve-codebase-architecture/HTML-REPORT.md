# Offline HTML report

Create one self-contained HTML file in the operating-system temporary directory.
The report must open with networking disabled: use embedded CSS, inline SVG, and
system fonts. Do not load remote scripts, fonts, stylesheets, or images.

## Structure

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Architecture review - {{repository}}</title>
    <style>
      :root {
        color-scheme: light;
        --paper: #fafaf9;
        --ink: #172033;
        --muted: #64748b;
        --line: #cbd5e1;
        --accent: #0f766e;
        --leak: #b91c1c;
        --warning: #92400e;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: var(--paper);
        color: var(--ink);
        font: 16px/1.5 system-ui, sans-serif;
      }
      main { width: min(1100px, 92vw); margin: 0 auto; padding: 3rem 0; }
      article { background: white; border: 1px solid var(--line); padding: 1.5rem; margin: 1.5rem 0; }
      .diagrams { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
      .badge { display: inline-block; border: 1px solid currentColor; padding: .15rem .5rem; }
      .files { color: var(--muted); font-family: ui-monospace, monospace; }
      .warning { border-left: .25rem solid var(--warning); padding-left: 1rem; }
      @media (max-width: 760px) { .diagrams { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <main>
      <header>...</header>
      <section id="candidates">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## Candidate cards

Each candidate includes:

- a short deepening title and `Strong`, `Worth exploring`, or `Speculative` badge;
- involved files;
- one observed problem and one proposed direction;
- test-seam impact and gains stated as leverage or locality;
- side-by-side before and after diagrams;
- a clearly marked conflict when an ADR would need reconsideration.

Use inline SVG for graphs, sequences, boxes and arrows. If a local Mermaid CLI
already rendered an SVG, embed or link that local SVG without adding a runtime
script. A basic inline-SVG diagram is the complete fallback.

Keep visuals compact and editorial. Use the `codebase-design` vocabulary:
module, interface, implementation, depth, deep, shallow, seam, adapter,
leverage, and locality.
