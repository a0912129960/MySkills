# Use copy-only skill installations

MySkills installs Managed Skills as copied deployment snapshots and does not support
Junction or symlink installation modes. Development uses the same explicit
validate-install-verify path as normal deployment, trading immediate source reflection for
stable active skills, reliable drift detection, portable installations, and less Windows
link-management complexity.
