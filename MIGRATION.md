# Migration Plan

Migration comes after the core capture/storage/retrieval model is validated.

## Rules

- Do not modify the original Obsidian vaults during initial import.
- Treat existing vaults as historical source repositories.
- Preserve source vault and source path.
- Preserve Markdown body, frontmatter, tags, wikilinks, and useful timestamps.
- Detect exact duplicates and link multiple sources to one canonical record where safe.
- Detect near duplicates and same-topic notes without merging away differences.
- Preserve conflicts and time-dependent changes instead of flattening them into one false current fact.

## Known local sources from reference-host inspection

These are historical/source locations observed on the reference machine. They are not to be modified in place during initial migration.

- `/home/damajha/Documents/Obsidian Vault`
- `/home/damajha/vaults/promiscunix`
- Other Obsidian-related paths exist but should be inspected later before import.

## Repeatable importer design

Planned importer stages:

1. Scan source files and compute content hashes.
2. Insert immutable source records.
3. Parse frontmatter/tags/wikilinks/timestamps.
4. Create raw archive records.
5. Run duplicate/near-duplicate detection.
6. Create candidate topic/project/person links.
7. Generate review reports before synthesis.
8. Only then create synthesized topic/project/person summaries.
