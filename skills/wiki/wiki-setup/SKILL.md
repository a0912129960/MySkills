---
name: wiki-setup
description: Create, connect, or repair the single configured MySkills Obsidian Wiki vault on Windows. Use only when the user explicitly asks to set up, connect, or repair the Wiki.
disable-model-invocation: true
---

# Wiki Setup

This workflow configures Wiki state; it does not install Skills, CLIs, hooks, or third-party
programs.

Determine whether the user is creating a vault, connecting an existing synchronized vault, or
repairing missing structure. Resolve the intended absolute Windows path. Invoke the
MySkills-managed launcher:

```powershell
$launcher = Join-Path $env:LOCALAPPDATA 'MySkills\bin\obsidian-wiki.cmd'
& $launcher setup --vault <absolute-path> --pretty
```

Preserve existing vault and `.obsidian` content. Create only missing safe defaults. When an
existing value is incompatible, show the conflict and require an explicit decision before
replacement. The first release has one config at `%USERPROFILE%\.obsidian-wiki\config`.

Optionally configure an existing QMD collection, but leave QMD installation and version
management to the MySkills installer. Report config path, vault path, created/preserved
artifacts, conflicts, CLI doctor result, and any manual next action.
