# MySkills

MySkills centralizes the skills selected for personal ownership while keeping discovered
but unapproved skills outside its management boundary.

## Language

**Candidate Skill**:
A skill discovered in a source repository or local installation that is awaiting an explicit management decision.
_Avoid_: Installed skill, managed skill

**Skill Origin**:
The repository or installation from which a Candidate Skill was discovered.
_Avoid_: Skill category, ownership

**Skill Category**:
The functional bucket under `skills/` in which a Managed Skill belongs, independent of where it originated.
_Avoid_: Skill origin, repository

**Managed Skill**:
A skill explicitly accepted into MySkills as its authoritative, editable copy.
_Avoid_: Candidate skill, discovered skill

**Provenance**:
The source repository, source commit, import date, and ownership record retained for an imported Managed Skill.
_Avoid_: Git history, installation source

**Executable Policy**:
A governance rule enforced by a manifest schema, CLI guard, validator, or automated test rather than relying on documentation alone.
_Avoid_: Guideline, undocumented convention

**Explicit-invocation Skill**:
A Managed Skill that enters a workflow only after the human explicitly names or invokes it; the AI must not select it implicitly on any supported platform.
_Avoid_: Human-only Skill, manual Skill

**Implicit-invocation Skill**:
A Managed Skill that the AI may select from the task context and Skill description without the human naming it; explicit invocation remains valid, and the classification is the same on every supported platform.
_Avoid_: Automatic Skill, AI-only Skill

**Skill Dependency**:
A third-party executable, runtime, CLI, or package required for a Managed Skill to work on a supported computer.
_Avoid_: Skill, bundled tool

**Runtime Prerequisite**:
A user-provided runtime whose presence and minimum version MySkills verifies but does not install. A missing or incompatible prerequisite blocks only the affected installation.
_Avoid_: Managed dependency, bundled runtime

**Installable Dependency**:
A third-party tool that MySkills is allowed to install after its required Runtime Prerequisites pass validation.
_Avoid_: Runtime prerequisite, bundled tool

**Machine Setup**:
The PowerShell-based, single-command process that installs eligible Managed Skills and their installable Skill Dependencies on another supported computer. It reports and skips installations whose Runtime Prerequisites are missing or incompatible.
_Avoid_: Bootstrap, skill copy, manual setup

**Supported Computer**:
A Windows computer on which MySkills guarantees that its installation and dependency-management workflows work.
_Avoid_: Any computer, cross-platform host
