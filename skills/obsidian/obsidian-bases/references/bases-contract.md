# Bases contract

Top-level keys are `filters`, `formulas`, `properties`, `summaries`, and
`views`. A filter is a string or an object containing exactly one of `and`,
`or`, or `not`; nested filter objects follow the same rule.

Properties may refer to note frontmatter directly, file metadata such as
`file.name`, `file.path`, `file.folder`, `file.ext`, `file.ctime`,
`file.mtime`, `file.tags`, and `file.links`, or a defined
`formula.<formula_name>`.

Common functions are `date`, `now`, `today`, `if`, `duration`, `file`, and
`link`. Subtracting dates returns a Duration. Access `.days`, `.hours`,
`.minutes`, `.seconds`, or `.milliseconds` before number methods:

```yaml
formulas:
  days_until_due: 'if(due, (date(due) - today()).days, "")'
```

Guard optional properties with `if`. Quote strings containing YAML punctuation.
Use single quotes around formulas that contain double-quoted literals.

A view supports:

```yaml
views:
  - type: table
    name: "Active"
    filters:
      and:
        - 'status == "active"'
    order:
      - file.name
      - status
      - formula.days_until_due
    groupBy:
      property: status
      direction: ASC
    summaries:
      formula.days_until_due: Average
```

Supported view types are `table`, `cards`, `list`, and `map`. Common built-in
summaries include `Average`, `Min`, `Max`, `Sum`, `Median`, `Stddev`,
`Earliest`, `Latest`, `Checked`, `Unchecked`, `Empty`, `Filled`, and `Unique`.
