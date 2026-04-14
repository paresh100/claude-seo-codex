#!/usr/bin/env bash
set -euo pipefail

main() {
    VENDOR_DIR="${HOME}/.codex/vendor/claude-seo"
    SKILL_DIR="${HOME}/.codex/skills/seo"

    echo "Removing Codex SEO wrapper"
    rm -rf "${SKILL_DIR}"
    rm -rf "${VENDOR_DIR}"
    echo "Removed ${SKILL_DIR} and ${VENDOR_DIR}"
}

main "$@"
