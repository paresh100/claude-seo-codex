---
name: seo-audit
description: "Full website SEO audit with parallel subagent delegation. Crawls up to 500 pages, detects business type, delegates to 10 specialists (7 core + 3 conditional), generates health score. Use when user says audit, full SEO check, analyze my site, or website health check."
user-invokable: true
argument-hint: "[url]"
license: MIT
metadata:
  author: paresh100
  version: "1.8.2"
  category: seo
---

# Full Website SEO Audit

## Process

1. **Fetch homepage**: use `scripts/fetch_page.py` to retrieve HTML
2. **Detect business type**: analyze homepage signals per seo orchestrator
3. **Crawl site**: follow internal links up to 500 pages, respect robots.txt
4. **Delegate to subagents in parallel** (if available, otherwise run inline sequentially):
   - `seo-technical` -- robots.txt, sitemaps, canonicals, Core Web Vitals, security headers
   - `seo-content` -- E-E-A-T, readability, thin content, AI citation readiness
   - `seo-schema` -- detection, validation, generation recommendations
   - `seo-sitemap` -- structure analysis, quality gates, missing pages
   - `seo-performance` -- LCP, INP, CLS measurements
   - `seo-visual` -- screenshots, mobile testing, above-fold analysis
   - `seo-geo` -- AI crawler access, llms.txt, citability, brand mention signals
   - `seo-google` -- Lighthouse, CWV field data (CrUX), URL indexation (GSC), organic traffic (GA4). **Always spawn** — runs Lighthouse regardless of whether Google API credentials are configured; CrUX/GSC/GA4 data is included when credentials are present (`python scripts/google_auth.py --check`)
   - `seo-local` -- GBP signals, NAP consistency, reviews, local schema (spawn when Local Service industry detected)
   - `seo-maps` -- Geo-grid rank tracking, GBP audit, review intelligence (spawn when Local Service detected AND DataForSEO MCP available)
   - `seo-backlinks` -- Domain authority, referring domains, anchor text, toxic links (spawn when Moz or Bing API credentials detected, or always for Common Crawl domain-level metrics)
5. **Score** -- aggregate into SEO Health Score (0-100) using category weights below
6. **Compile** -- after all subagents complete, merge their outputs into a single `unified-audit-data.json` matching this schema:
   ```json
   {
     "domain": "example.com",
     "date": "YYYY-MM-DD",
     "business_type": "...",
     "pages_crawled": 131,
     "overall_score": 48,
     "scores": {
       "technical": 54, "content": 54, "on_page": 48,
       "schema": 22, "performance": 45, "geo": 38, "images": 62
     },
     "critical_issues": [{"title":"...","detail":"...","severity":"CRITICAL"}],
     "quick_wins": [{"text":"...","effort":"1 hour"}],
     "technical": {
       "findings": [{"category":"...","finding":"...","severity":"CRITICAL","fix":"..."}],
       "stack": {"CMS": "WordPress 6.9", "Server": "nginx/Plesk"}
     },
     "content": {
       "eeat": {
         "experience": {"score": 38, "finding": "..."},
         "expertise": {"score": 52, "finding": "..."},
         "authoritativeness": {"score": 45, "finding": "..."},
         "trustworthiness": {"score": 61, "finding": "..."}
       },
       "gaps": [{"title":"...","detail":"...","priority":"high"}]
     },
     "on_page": {
       "pages": [{"page":"Homepage","title_chars":67,"meta_description":"...","h1_count":2,"issues":"..."}]
     },
     "schema": {"present":["Organization"],"missing":["Product"],"errors":[]},
     "performance": {
       "lighthouse": {"performance":45,"accessibility":68,"best_practices":55,"seo":64},
       "crux": {
         "LCP": {"p75":"3800ms","rating":"NEEDS_IMPROVEMENT","good_pct":28,"ni_pct":42,"poor_pct":30},
         "INP": {"p75":"380ms","rating":"NEEDS_IMPROVEMENT","good_pct":42,"ni_pct":35,"poor_pct":23},
         "CLS": {"p75":"0.220","rating":"NEEDS_IMPROVEMENT","good_pct":35,"ni_pct":40,"poor_pct":25},
         "FCP": {"p75":"2100ms","rating":"NEEDS_IMPROVEMENT","good_pct":48,"ni_pct":32,"poor_pct":20},
         "TTFB": {"p75":"320ms","rating":"GOOD","good_pct":72,"ni_pct":20,"poor_pct":8}
       },
       "failed_audits": [{"title":"...","score":0.15,"detail":"..."}]
     },
     "geo": {
       "platforms": {
         "Google AI Overviews": {"score":55,"bottleneck":"..."},
         "ChatGPT": {"score":65,"bottleneck":"..."},
         "Perplexity": {"score":60,"bottleneck":"..."},
         "Bing Copilot": {"score":50,"bottleneck":"..."}
       },
       "findings": [{"text":"..."}]
     },
     "images": {"findings":[{"title":"...","detail":"...","severity":"medium"}]},
     "backlinks": {"domain_authority":32,"referring_domains":180,"total_backlinks":920,"findings":[]},
     "action_plan": [{"priority":"CRITICAL","title":"...","detail":"...","effort":"1 hour","impact":"High"}],
     "roadmap": []
   }
   ```
7. **Generate PDF** -- run the unified report generator automatically — do not ask the user:
   ```bash
   python scripts/unified_report.py --data unified-audit-data.json --domain <domain> --output-dir .
   ```
   This produces a single professional A4 PDF combining all sections (Technical, Content, On-Page, Schema, Performance with real CrUX, GEO, Images, Backlinks, Action Plan, Roadmap). Report is named `SEO-Full-Audit-<domain>-<date>.pdf`.

## Crawl Configuration

```
Max pages: 500
Respect robots.txt: Yes
Follow redirects: Yes (max 3 hops)
Timeout per page: 30 seconds
Concurrent requests: 5
Delay between requests: 1 second
```

## Output Files

- `unified-audit-data.json`: Merged JSON from all subagents (input to report generator)
- `SEO-Full-Audit-<domain>-<date>.pdf`: Single unified PDF report (all categories)
- `SEO-Full-Audit-<domain>-<date>.html`: HTML version of the same report
- `ACTION-PLAN.md`: Prioritized recommendations (Critical > High > Medium > Low)
- `screenshots/`: Desktop + mobile captures (if Playwright available)

## Scoring Weights

| Category | Weight |
|----------|--------|
| Technical SEO | 22% |
| Content Quality | 23% |
| On-Page SEO | 20% |
| Schema / Structured Data | 10% |
| Performance (CWV) | 10% |
| AI Search Readiness | 10% |
| Images | 5% |

## Report Structure

The unified PDF contains all of the following sections in order:

1. Cover page — domain, overall score, date, business type
2. Table of Contents — with scores per category
3. Executive Summary — metric cards, category gauges chart, top 5 critical issues, top 5 quick wins
4. Technical SEO — findings table (category, finding, severity, fix) + tech stack detected
5. Content Quality & E-E-A-T — 4-dimension scores table + content gaps
6. On-Page SEO — per-page analysis (title, meta, H1, issues)
7. Schema / Structured Data — detected types, missing schema, validation errors
8. Performance & Core Web Vitals — Lighthouse gauges, CrUX field data with stacked bar chart, failed audits
9. AI Search Readiness (GEO) — platform scores (Google AI Overviews, ChatGPT, Perplexity, Bing Copilot)
10. Images — findings
11. Backlink Profile — DA, referring domains, total backlinks (if data available)
12. Prioritised Action Plan — grouped by Critical / High / Medium / Low with effort + impact
13. Implementation Roadmap — 4-phase table

## Priority Definitions

- **Critical**: Blocks indexing or causes penalties (fix immediately)
- **High**: Significantly impacts rankings (fix within 1 week)
- **Medium**: Optimisation opportunity (fix within 1 month)
- **Low**: Nice to have (backlog)

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, spawn the `seo-dataforseo` agent alongside existing subagents to enrich the audit with live data: real SERP positions, backlink profiles with spam scores, on-page analysis (Lighthouse), business listings, and AI visibility checks.

## Error Handling

| Scenario | Action |
|----------|--------|
| URL unreachable (DNS failure, connection refused) | Report the error clearly. Do not guess site content. Suggest the user verify the URL and try again. |
| robots.txt blocks crawling | Report which paths are blocked. Analyse only accessible pages and note the limitation in the report. |
| Rate limiting (429 responses) | Back off and reduce concurrent requests. Report partial results with a note on which sections could not be completed. |
| Timeout on large sites (500+ pages) | Cap the crawl at the timeout limit. Report findings for pages crawled and estimate total site scope. |
| Google API credentials not configured | Continue without GSC/GA4/CrUX data. seo-google still runs Lighthouse. Note missing data in the performance section. |
| unified_report.py fails (missing weasyprint/matplotlib) | Fall back to writing FULL-AUDIT-REPORT.md and ACTION-PLAN.md. Inform the user to run `pip install weasyprint matplotlib` for PDF output. |
