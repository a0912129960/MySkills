# Use copy-only skill installations

MySkills installs Managed Skills as copied deployment snapshots and does not support
Junction or symlink installation modes. Development uses the same explicit
validate-install-verify path as normal deployment, trading immediate source reflection for
stable active skills, reliable drift detection, portable installations, and less Windows
link-management complexity.

A pre-existing Junction or symbolic link is an installation conflict, not a supported
deployment mode. After explicit `-ReplaceLinks` authorization, the installer may migrate that
entry to the copy-only model by preserving the link, installing and verifying an independent
snapshot, and only then removing the preserved link object. The linked destination is never
modified, and any failed copy verification restores the original link. Other
reparse-point types remain blocked. This migration is exception-safe, not power-loss atomic:
forced termination may leave the preserved link as a `.myskills-previous-link-*` sibling,
which must not be deleted and requires recovery review before installation is rerun.
