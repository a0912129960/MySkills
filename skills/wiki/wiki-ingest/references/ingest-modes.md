# Ingest modes

- File: parse one supported local source and retain its canonical path and digest.
- Folder: plan bounded batches, respect exclusions, and record each source independently.
- Structured data: preserve field meaning, identifiers, and rejected-record counts.
- Conversation/export: retain durable knowledge and privacy boundaries, not the raw transcript.
- Code: use deterministic AST extraction only when code files are present, then verify semantic
  claims against source.
- URL: retrieve with the active agent's native network tools and record URL, title, publisher,
  retrieval date, and limitations.
- Raw: promote bounded drafts from `_raw/` only after validating their sources and content.
- Image/PDF: use active-agent native capabilities and explicitly report unreadable pages,
  unsupported media, or OCR uncertainty.

Never require optional source-repository packages. QMD is acceleration only.
