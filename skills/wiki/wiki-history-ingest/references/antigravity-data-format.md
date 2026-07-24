# Antigravity history source

Default root: `%USERPROFILE%\.gemini\antigravity-cli`, overridable by
`ANTIGRAVITY_HISTORY_PATH` in local Wiki configuration.

Use `conversation_summaries.db` to identify conversations, then read validated
`brain\<conversation-id>\.system_generated\logs\transcript.jsonl` records. SQLite access uses
Python's standard library. Validate required tables, identifiers, containment under the
history root, JSON objects, roles, timestamps, and content before emitting records.

Do not parse internal protobuf files, per-conversation databases, or format-unstable
`history.jsonl`. An unknown schema or record shape is a safe failure, not an empty successful
ingest.
