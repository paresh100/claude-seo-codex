# Running Claude SEO in Codex

This repository targets Claude Code out of the box, but you can use it in Codex with the included wrapper installer.

## Install

From a local clone:

```bash
bash install-codex.sh
```

That installer will:

- copy this repo to `~/.codex/vendor/claude-seo`
- create a Codex skill at `~/.codex/skills/seo`
- install Python dependencies into `~/.codex/vendor/claude-seo/.venv` when possible
- enable OS-native trust-store support for more reliable HTTPS requests

## Use in Codex

Codex works best with natural-language requests, but this adaptation also
includes a small slash-command shim for the most common Claude-style commands.

Examples:

```text
audit https://example.com for SEO
review the schema on https://example.com/pricing
run a technical SEO audit for https://example.com
analyze backlinks for https://example.com
```

Supported slash-command shim:

```text
/seo
/seo audit https://example.com
/seo backlinks https://example.com
/seo images serp digital marketing agency
/seo images optimize /path/to/image.jpg
```

See [codex-commands.md](codex-commands.md) for the command list.

## Remove

```bash
bash ~/.codex/vendor/claude-seo/uninstall-codex.sh
```
