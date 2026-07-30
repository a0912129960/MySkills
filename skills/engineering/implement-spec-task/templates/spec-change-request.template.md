# Spec Change Request

## Request

- Request ID:
- Task ID:
- Current Manifest:
- Current lifecycle state: `spec-revision-required`

## Code Evidence

- Observed implementation fact:
- Reproduction or inspection:
- Evidence paths:

## Classification

- Behavior gap / solution gap / Task boundary gap / validation gap / current-rule conflict:

## Return Level

- Gate 1 / Gate 2 / Task Plan Gate:
- Reason:

## Affected Normative Artifacts

| Artifact | Required Decision Or Change | Downstream Invalidation |
|---|---|---|

## Partial Change State

- Production files already changed:
- Tests or evidence already created:
- Safe to retain while awaiting revision:
- Revert or isolation needed:

## Human-Authorized Revision Invocation

`$spec-package-generator <feature-package-path> --revise-from <spec-change-request-path>`

The executor must stop here. It must not edit normative artifacts or invoke the
generator automatically.
