# Properties

Properties are YAML frontmatter at the beginning of the note:

```yaml
---
title: My Note
date: 2026-07-24
tags:
  - project
aliases:
  - Alternative Name
cssclasses:
  - custom-class
---
```

Use YAML lists for multiple values. Quote ambiguous scalars and strings
containing YAML punctuation. Tags may contain letters, numbers (not as the
first character), underscores, hyphens, and forward slashes.
