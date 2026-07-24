# JSON Canvas contract

The root contains optional `nodes` and `edges` arrays.

Every node requires `id`, `type`, `x`, `y`, `width`, and `height`.

| Type | Required payload |
| --- | --- |
| `text` | `text` containing plain text or Markdown |
| `file` | `file`; optional `subpath` begins with `#` |
| `link` | `url` |
| `group` | optional `label`, `background`, and `backgroundStyle` |

`backgroundStyle` is `cover`, `ratio`, or `repeat`.

Every edge requires `id`, `fromNode`, and `toNode`. Optional `fromSide` and
`toSide` are `top`, `right`, `bottom`, or `left`; optional `fromEnd` and
`toEnd` are `none` or `arrow`.

Colors are presets `"1"` through `"6"` or hexadecimal strings. Coordinates may
be negative. Array order controls z-order: later nodes render above earlier
nodes.

Example:

```json
{
  "nodes": [
    {
      "id": "6f0ad84f44ce9c17",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 320,
      "height": 160,
      "text": "# Start"
    }
  ],
  "edges": []
}
```
