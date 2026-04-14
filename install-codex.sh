#!/usr/bin/env bash
set -euo pipefail

main() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VENDOR_DIR="${HOME}/.codex/vendor/claude-seo"
    SKILL_DIR="${HOME}/.codex/skills/seo"
    VENV_DIR="${VENDOR_DIR}/.venv"

    echo "========================================"
    echo "  Claude SEO -> Codex installer"
    echo "========================================"
    echo ""

    command -v python3 >/dev/null 2>&1 || {
        echo "Python 3 is required but was not found."
        exit 1
    }

    mkdir -p "${HOME}/.codex/vendor" "${HOME}/.codex/skills"
    rm -rf "${VENDOR_DIR}" "${SKILL_DIR}"

    echo "Copying repo into ${VENDOR_DIR}"
    mkdir -p "${VENDOR_DIR}"
    cp -R "${SCRIPT_DIR}/." "${VENDOR_DIR}/"
    rm -rf "${VENDOR_DIR}/.git" "${VENDOR_DIR}/.venv"

    echo "Installing Codex wrapper skill into ${SKILL_DIR}"
    mkdir -p "${SKILL_DIR}"
    cat > "${SKILL_DIR}/SKILL.md" <<EOF
---
name: seo
description: Comprehensive SEO analysis for websites and local businesses. Use when the user asks for SEO audits, page reviews, schema checks, technical SEO, Core Web Vitals, GEO/AI search, sitemaps, backlinks, local SEO, hreflang, or Google SEO API reporting.
metadata:
  source: claude-seo
  vendor-path: ${VENDOR_DIR}
---

# SEO for Codex

This skill is a Codex wrapper around the vendor content installed at:

\`${VENDOR_DIR}\`

## Invocation model

- Do not expect Claude slash commands.
- Interpret natural-language requests directly.
- If the user writes a Claude-style command such as \`/seo audit https://example.com\`, treat it as a normal request to audit that site.

## Routing

- Full website audit: load \`${VENDOR_DIR}/skills/seo-audit/SKILL.md\`
- Single page review: load \`${VENDOR_DIR}/skills/seo-page/SKILL.md\`
- Technical SEO: load \`${VENDOR_DIR}/skills/seo-technical/SKILL.md\`
- Content / E-E-A-T: load \`${VENDOR_DIR}/skills/seo-content/SKILL.md\`
- Schema markup: load \`${VENDOR_DIR}/skills/seo-schema/SKILL.md\`
- Images / image SEO: load \`${VENDOR_DIR}/skills/seo-images/SKILL.md\`
- Sitemap work: load \`${VENDOR_DIR}/skills/seo-sitemap/SKILL.md\`
- GEO / AI search: load \`${VENDOR_DIR}/skills/seo-geo/SKILL.md\`
- Strategic SEO plan: load \`${VENDOR_DIR}/skills/seo-plan/SKILL.md\`
- Programmatic SEO: load \`${VENDOR_DIR}/skills/seo-programmatic/SKILL.md\`
- Competitor pages: load \`${VENDOR_DIR}/skills/seo-competitor-pages/SKILL.md\`
- Local SEO: load \`${VENDOR_DIR}/skills/seo-local/SKILL.md\`
- Maps intelligence: load \`${VENDOR_DIR}/skills/seo-maps/SKILL.md\`
- Hreflang: load \`${VENDOR_DIR}/skills/seo-hreflang/SKILL.md\`
- Google SEO APIs and PDF reports: load \`${VENDOR_DIR}/skills/seo-google/SKILL.md\`
- Backlinks: load \`${VENDOR_DIR}/skills/seo-backlinks/SKILL.md\`
- DataForSEO extension: load \`${VENDOR_DIR}/skills/seo-dataforseo/SKILL.md\`
- AI image generation extension: load \`${VENDOR_DIR}/skills/seo-image-gen/SKILL.md\`

## Shared paths

- Shared scripts: \`${VENDOR_DIR}/scripts\`
- Core references: \`${VENDOR_DIR}/skills/seo/references\`
- Agent notes: \`${VENDOR_DIR}/agents\`

## Execution rules

- When a source skill references \`scripts/...py\`, run the script from \`${VENDOR_DIR}/scripts\`.
- Prefer \`${VENDOR_DIR}/.venv/bin/python\` when that virtualenv exists; otherwise use \`python3\`.
- Load only the specific source skill and reference files needed for the current request.
- Keep work local by default. If a source file suggests spawning subagents, only delegate when the user explicitly asks for parallel agents or delegation.
- Treat agent markdown files under \`${VENDOR_DIR}/agents\` as specialist reference notes, not as mandatory runtime workers.
- Keep the upstream scoring rules, quality gates, and SEO policy guidance intact unless the user asks to override them.

## Compatibility notes

- The upstream docs use Claude slash commands like \`/seo audit\`. In Codex, the equivalent is a plain request such as "run a full SEO audit for https://example.com".
- The upstream plugin marketplace instructions do not apply here. This wrapper is the Codex entrypoint.
EOF

    cat > "${SKILL_DIR}/README.md" <<EOF
This skill was installed by:
  ${VENDOR_DIR}/install-codex.sh

Remove it with:
  bash "${VENDOR_DIR}/uninstall-codex.sh"
EOF

    echo "Creating Python virtualenv"
    if python3 -m venv "${VENV_DIR}" 2>/dev/null; then
        if "${VENV_DIR}/bin/pip" install --quiet -r "${VENDOR_DIR}/requirements.txt"; then
            echo "Installed Python dependencies into ${VENV_DIR}"
        else
            echo "Dependency install failed. Retry manually:"
            echo "  ${VENV_DIR}/bin/pip install -r ${VENDOR_DIR}/requirements.txt"
        fi
    else
        echo "Could not create a virtualenv automatically."
        echo "Manual fallback:"
        echo "  python3 -m pip install --user -r ${VENDOR_DIR}/requirements.txt"
    fi

    echo ""
    echo "Codex install complete."
    echo ""
    echo "Restart Codex, then use prompts such as:"
    echo "  audit https://example.com for SEO"
    echo "  review the schema on https://example.com/product/widget"
    echo "  run a local SEO audit for https://example.com"
    echo ""
    echo "If you want to remove it later:"
    echo "  bash ${VENDOR_DIR}/uninstall-codex.sh"
}

main "$@"
