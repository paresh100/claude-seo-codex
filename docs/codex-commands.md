# Codex Slash-Command Shim

This Codex adaptation supports a small Claude-style command surface directly in chat.

## Supported commands

```text
/seo
/seo audit <url>
/seo backlinks <url>
/seo images serp <keyword>
/seo images optimize <path>
```

## Behavior

- `/seo`
  Prints a compact command list with usage examples.
- `/seo audit <url>`
  Routes to the full audit skill.
- `/seo backlinks <url>`
  Routes to the backlink analysis skill.
- `/seo images serp <keyword>`
  Routes to the image SERP workflow from `seo-images`.
- `/seo images optimize <path>`
  Routes to the local image optimization workflow from `seo-images`.

## Unsupported commands

If the user enters another `/seo ...` subcommand, the Codex wrapper should:

1. explain that the slash-command shim currently supports only the commands above
2. show `/seo` help
3. suggest the equivalent natural-language request for anything more advanced
