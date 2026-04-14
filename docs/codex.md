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

Codex does not use Claude slash commands. Ask naturally instead.

Examples:

```text
audit https://example.com for SEO
review the schema on https://example.com/pricing
run a technical SEO audit for https://example.com
analyze backlinks for https://example.com
```

If you paste a Claude command such as `/seo audit https://example.com`, the wrapper skill is designed to treat that as a normal request.

## Remove

```bash
bash ~/.codex/vendor/claude-seo/uninstall-codex.sh
```
