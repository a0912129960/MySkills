# Configuration

The first MySkills release supports one configured vault. Resolve it through the
MySkills-managed launcher:

```powershell
$launcher = Join-Path $env:LOCALAPPDATA 'MySkills\bin\obsidian-wiki.cmd'
& $launcher config resolve --cwd (Get-Location).Path --pretty
```

Continue only when the JSON result is `resolved`. `invalid` means an explicit configuration is
broken and must be repaired; do not fall through to another location. `not-found` permits
offering `wiki-setup`.

Per-computer configuration lives at `%USERPROFILE%\.obsidian-wiki\config`. Read only required
keys and never print unrelated values. Runtime references to a former repository clone are
invalid.
