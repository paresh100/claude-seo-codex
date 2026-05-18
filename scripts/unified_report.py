#!/usr/bin/env python3
"""
Unified SEO Audit Report Generator.

Takes JSON output from the full seo-audit orchestrator (all subagents combined)
and generates a single professional PDF report.

Usage:
    python unified_report.py --data audit-data.json --domain example.com
    python unified_report.py --data audit-data.json --domain example.com --output-dir ./reports
    cat audit-data.json | python unified_report.py --domain example.com

Expected JSON schema (all fields optional except domain):
{
  "domain": "example.com",
  "date": "2026-05-18",
  "business_type": "B2B SaaS",
  "pages_crawled": 131,
  "overall_score": 48,
  "scores": {
    "technical": 54, "content": 54, "on_page": 48,
    "schema": 22, "performance": 45, "geo": 38, "images": 62
  },
  "critical_issues": [{"title": "...", "detail": "...", "severity": "CRITICAL"}],
  "quick_wins": [{"text": "...", "effort": "1 hour"}],
  "technical": {
    "findings": [{"category": "Security Headers", "finding": "...", "severity": "CRITICAL", "fix": "..."}],
    "stack": {"CMS": "WordPress 6.9", "Server": "nginx"}
  },
  "content": {
    "eeat": {
      "experience": {"score": 38, "finding": "..."},
      "expertise": {"score": 52, "finding": "..."},
      "authoritativeness": {"score": 45, "finding": "..."},
      "trustworthiness": {"score": 61, "finding": "..."}
    },
    "gaps": [{"title": "...", "detail": "...", "priority": "high"}]
  },
  "on_page": {
    "pages": [{"page": "Homepage", "title_chars": 67, "meta_description": "...", "h1_count": 2, "issues": "..."}]
  },
  "schema": {"present": ["Organization", "WebSite"], "missing": ["Product"], "errors": []},
  "performance": {
    "lighthouse": {"performance": 45, "accessibility": 68, "best_practices": 55, "seo": 64},
    "crux": {
      "LCP": {"p75": "3800ms", "rating": "NEEDS_IMPROVEMENT", "good_pct": 28, "ni_pct": 42, "poor_pct": 30},
      "INP": {"p75": "380ms", "rating": "NEEDS_IMPROVEMENT", "good_pct": 42, "ni_pct": 35, "poor_pct": 23},
      "CLS": {"p75": "0.220", "rating": "NEEDS_IMPROVEMENT", "good_pct": 35, "ni_pct": 40, "poor_pct": 25},
      "FCP": {"p75": "2100ms", "rating": "NEEDS_IMPROVEMENT", "good_pct": 48, "ni_pct": 32, "poor_pct": 20},
      "TTFB": {"p75": "320ms", "rating": "GOOD", "good_pct": 72, "ni_pct": 20, "poor_pct": 8}
    },
    "failed_audits": [{"title": "...", "score": 0.15, "detail": "..."}]
  },
  "geo": {
    "platforms": {
      "Google AI Overviews": {"score": 55, "bottleneck": "Thin tool pages"},
      "ChatGPT": {"score": 65, "bottleneck": "No external entity signals"},
      "Perplexity": {"score": 60, "bottleneck": "No inline source hyperlinks"},
      "Bing Copilot": {"score": 50, "bottleneck": "No entity presence"}
    },
    "findings": [{"text": "No llms.txt found"}]
  },
  "images": {"findings": [{"title": "...", "detail": "...", "severity": "medium"}]},
  "backlinks": {"domain_authority": 32, "referring_domains": 180, "total_backlinks": 920, "findings": []},
  "action_plan": [{"priority": "CRITICAL", "title": "...", "detail": "...", "effort": "1 hour", "impact": "High"}],
  "roadmap": []
}
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib required. pip install matplotlib", file=sys.stderr)
    sys.exit(1)

try:
    from weasyprint import HTML
except ImportError:
    print("Error: weasyprint required. pip install weasyprint", file=sys.stderr)
    sys.exit(1)


# ─── Brand ───────────────────────────────────────────────────────────────────

BRAND = {
    "primary":   "#1e3a5f",
    "secondary": "#4a5568",
    "accent":    "#b8860b",
    "success":   "#2d6a4f",
    "warning":   "#d4740e",
    "danger":    "#c53030",
    "light_bg":  "#faf9f7",
    "grid":      "#d6d3cc",
    "muted":     "#6b7280",
}


def _score_color(score):
    s = int(score) if score else 0
    if s >= 80:
        return BRAND["success"]
    elif s >= 50:
        return BRAND["warning"]
    return BRAND["danger"]


def _rating_color(rating):
    r = str(rating).lower().replace("-", "_").replace(" ", "_")
    if r in ("good", "pass", "fast"):
        return BRAND["success"]
    elif "needs" in r or r == "average":
        return BRAND["warning"]
    return BRAND["danger"]


# ─── Charts ──────────────────────────────────────────────────────────────────

def chart_overall_donut(score: int, chart_dir: Path) -> str:
    color = _score_color(score)
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.pie(
        [score, 100 - score],
        colors=[color, "#e8e8e8"],
        startangle=90,
        wedgeprops={"width": 0.4, "edgecolor": "white"},
        counterclock=False,
    )
    ax.text(0, 0.05, str(score), ha="center", va="center",
            fontsize=28, fontweight="bold", color=color)
    ax.text(0, -0.28, "/100", ha="center", va="center",
            fontsize=11, color=BRAND["muted"])
    fig.patch.set_facecolor("white")
    path = chart_dir / "chart_overall.png"
    plt.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def chart_category_gauges(scores: dict, chart_dir: Path) -> str:
    cats = [
        ("Technical", scores.get("technical", 0)),
        ("Content",   scores.get("content",   0)),
        ("On-Page",   scores.get("on_page",   0)),
        ("Schema",    scores.get("schema",     0)),
        ("Perf",      scores.get("performance",0)),
        ("GEO",       scores.get("geo",        0)),
        ("Images",    scores.get("images",     0)),
    ]
    fig, axes = plt.subplots(1, len(cats), figsize=(14, 2.6))
    for ax, (label, score) in zip(axes, cats):
        color = _score_color(score)
        ax.pie(
            [score, 100 - score],
            colors=[color, "#e8e8e8"],
            startangle=90,
            wedgeprops={"width": 0.35, "edgecolor": "white"},
            counterclock=False,
        )
        ax.text(0, 0.08, str(int(score)), ha="center", va="center",
                fontsize=13, fontweight="bold", color=color)
        ax.text(0, -0.28, label, ha="center", va="center",
                fontsize=7, color=BRAND["secondary"])
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.4)
    path = chart_dir / "chart_gauges.png"
    plt.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def chart_cwv_bars(crux: dict, chart_dir: Path) -> str:
    metrics = ["LCP", "INP", "CLS", "FCP", "TTFB"]
    labels, good, ni, poor = [], [], [], []
    for m in metrics:
        d = crux.get(m, {})
        if d:
            labels.append(m)
            good.append(d.get("good_pct", 0))
            ni.append(d.get("ni_pct", 0))
            poor.append(d.get("poor_pct", 0))
    if not labels:
        return ""
    y = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(7, 2.5))
    ax.barh(y, good, color=BRAND["success"], label="Good")
    ax.barh(y, ni, left=good, color=BRAND["warning"], label="Needs Improvement")
    ax.barh(y, poor, left=[g + n for g, n in zip(good, ni)], color=BRAND["danger"], label="Poor")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("% of page loads", fontsize=8)
    ax.set_xlim(0, 100)
    ax.legend(fontsize=7, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    path = chart_dir / "chart_cwv.png"
    plt.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


# ─── CSS ─────────────────────────────────────────────────────────────────────

def _css() -> str:
    p = BRAND["primary"]
    s = BRAND["secondary"]
    g = BRAND["grid"]
    m = BRAND["muted"]
    return f"""
@page {{
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-size: 8pt; color: {m};
    }}
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Georgia, "Times New Roman", serif; font-size: 9pt; color: {s}; background: white; line-height: 1.5; }}
h1 {{ font-size: 22pt; color: {p}; margin-bottom: 8px; }}
h2 {{ font-size: 13pt; color: {p}; border-bottom: 2px solid {p}; padding-bottom: 4px; margin: 20px 0 10px; }}
h3 {{ font-size: 10pt; color: {p}; margin: 12px 0 6px; }}
p {{ margin-bottom: 6px; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 8pt; }}
th {{ background: {p}; color: white; padding: 6px 8px; text-align: left; font-weight: bold; }}
td {{ padding: 5px 8px; border-bottom: 1px solid {g}; vertical-align: top; }}
tr:nth-child(even) td {{ background: #f8f8f8; }}
.break {{ page-break-before: always; }}
.cover {{ text-align: center; padding: 60px 0; }}
.cover-meta {{ margin-top: 40px; font-size: 9pt; color: {m}; }}
.cards {{ display: flex; gap: 10px; margin: 12px 0; flex-wrap: wrap; }}
.card {{ flex: 1; min-width: 70px; border: 1px solid {g}; border-radius: 4px; padding: 10px; text-align: center; }}
.card .val {{ font-size: 17pt; font-weight: bold; }}
.card .lbl {{ font-size: 7pt; color: {m}; text-transform: uppercase; letter-spacing: 0.5px; }}
.chip {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-weight: bold; font-size: 8.5pt; color: white; }}
.badge-critical {{ color: white; background: {BRAND['danger']}; padding: 2px 6px; border-radius: 3px; font-size: 7pt; font-weight: bold; }}
.badge-high {{ color: white; background: #c05621; padding: 2px 6px; border-radius: 3px; font-size: 7pt; font-weight: bold; }}
.badge-medium {{ color: white; background: {BRAND['warning']}; padding: 2px 6px; border-radius: 3px; font-size: 7pt; font-weight: bold; }}
.badge-low {{ color: {p}; background: #e8f0fe; padding: 2px 6px; border-radius: 3px; font-size: 7pt; font-weight: bold; }}
.badge-pass {{ color: white; background: {BRAND['success']}; padding: 2px 6px; border-radius: 3px; font-size: 7pt; font-weight: bold; }}
.issue {{ border-left: 4px solid {BRAND['danger']}; padding: 8px 12px; margin: 6px 0; background: #fff5f5; }}
.issue.high {{ border-color: #c05621; background: #fff8f3; }}
.issue.medium {{ border-color: {BRAND['warning']}; background: #fffbf0; }}
.win {{ border-left: 4px solid {BRAND['success']}; padding: 8px 12px; margin: 6px 0; background: #f0fff4; }}
.caption {{ font-size: 7pt; color: {m}; text-align: center; margin-top: 4px; font-style: italic; }}
.toc-row {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted {g}; font-size: 9pt; }}
.footer {{ font-size: 7pt; color: {m}; margin-top: 20px; border-top: 1px solid {g}; padding-top: 8px; }}
img {{ max-width: 100%; height: auto; }}
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _img(path, alt="", style=""):
    if not path or not os.path.exists(str(path)):
        return ""
    uri = Path(path).as_uri()
    s = f' style="{style}"' if style else ""
    return f'<img src="{uri}" alt="{alt}"{s}>'


def _chip(score) -> str:
    color = _score_color(score)
    return f'<span class="chip" style="background:{color}">{score}</span>'


def _badge(sev: str) -> str:
    cls = sev.lower() if sev.lower() in ("critical", "high", "medium", "low", "pass") else "medium"
    return f'<span class="badge-{cls}">{sev}</span>'


# ─── Section builders ────────────────────────────────────────────────────────

def s_cover(data: dict, chart_dir: Path) -> str:
    domain   = data.get("domain", "")
    date     = data.get("date", datetime.now().strftime("%d %B %Y"))
    biz      = data.get("business_type", "")
    overall  = int(data.get("overall_score", 0))
    donut    = chart_overall_donut(overall, chart_dir)
    rating   = "Good" if overall >= 80 else "Needs Improvement" if overall >= 50 else "Poor"
    color    = _score_color(overall)
    return f"""
<div class="cover">
  <h1 style="font-size:28pt;letter-spacing:1px">{domain}</h1>
  <p style="font-size:11pt;color:{BRAND['muted']};margin-top:6px">Full SEO Audit Report — {biz}</p>
  <div style="margin:28px auto;width:160px">{_img(donut,"Overall score")}</div>
  <p style="font-size:11pt;font-weight:bold;color:{color}">SEO HEALTH SCORE — {rating.upper()}</p>
  <div class="cover-meta">
    <p><strong>Domain:</strong> {domain} &nbsp;|&nbsp; <strong>Date:</strong> {date}</p>
    <p style="margin-top:8px;font-size:8pt">Produced by Paresh M Patel</p>
  </div>
</div>"""


def s_toc(data: dict) -> str:
    scores  = data.get("scores", {})
    has_bl  = bool(data.get("backlinks"))
    entries = [
        ("Executive Summary",                  2,  None),
        ("Technical SEO",                      3,  scores.get("technical")),
        ("Content Quality & E-E-A-T",          4,  scores.get("content")),
        ("On-Page SEO",                        5,  scores.get("on_page")),
        ("Schema / Structured Data",           5,  scores.get("schema")),
        ("Performance & Core Web Vitals",      6,  scores.get("performance")),
        ("AI Search Readiness (GEO)",          6,  scores.get("geo")),
        ("Images",                             7,  scores.get("images")),
        ("Backlink Profile",                   7,  scores.get("backlinks")),
        ("Prioritised Action Plan",            8,  None),
        ("Implementation Roadmap",             9,  None),
    ]
    rows = ""
    for title, page, score in entries:
        if title == "Backlink Profile" and not has_bl:
            continue
        chip = f" &nbsp; {_chip(score)}" if score is not None else ""
        rows += f'<div class="toc-row"><span>{title}{chip}</span><span>p.{page}</span></div>\n'
    return f"<h2>Table of Contents</h2>{rows}"


def s_executive(data: dict, chart_dir: Path) -> str:
    scores  = data.get("scores", {})
    gauges  = chart_category_gauges(scores, chart_dir)
    criticals = data.get("critical_issues", [])
    wins    = data.get("quick_wins", [])

    cards = ""
    for label, key in [("Technical","technical"),("Content","content"),("On-Page","on_page"),
                       ("Schema","schema"),("Performance","performance"),("GEO","geo"),("Images","images")]:
        s = scores.get(key, 0)
        cards += f'<div class="card"><div class="val" style="color:{_score_color(s)}">{s}</div><div class="lbl">{label}</div></div>'

    crit_html = ""
    for item in criticals[:5]:
        title  = item.get("title",  item) if isinstance(item, dict) else str(item)
        detail = item.get("detail", "")  if isinstance(item, dict) else ""
        sev    = item.get("severity","critical") if isinstance(item, dict) else "critical"
        crit_html += f'<div class="issue"><strong>{_badge(sev.upper())} {title}</strong>'
        if detail:
            crit_html += f'<p style="margin-top:4px;font-size:8pt">{detail}</p>'
        crit_html += "</div>"

    wins_html = ""
    for item in wins[:5]:
        text   = item.get("text",   item) if isinstance(item, dict) else str(item)
        effort = item.get("effort", "")   if isinstance(item, dict) else ""
        wins_html += f'<div class="win">✓ {text}'
        if effort:
            wins_html += f' <em style="color:{BRAND["muted"]}">({effort})</em>'
        wins_html += "</div>"

    return f"""
<div class="break"></div>
<h2>Executive Summary</h2>
<div class="cards">{cards}</div>
{_img(gauges,"Category scores") if gauges else ""}
<p class="caption">SEO health scores by category</p>
<h3>Top Critical Issues</h3>
{crit_html or "<p>No critical issues found.</p>"}
<h3 style="margin-top:14px">Top Quick Wins (Same Day — Zero User Impact)</h3>
{wins_html or "<p>No quick wins identified.</p>"}
"""


def s_technical(data: dict) -> str:
    tech     = data.get("technical", {})
    score    = data.get("scores", {}).get("technical", 0)
    findings = tech.get("findings", [])
    stack    = tech.get("stack", {})

    rows = ""
    for f in findings:
        rows += (f"<tr><td><strong>{f.get('category','')}</strong></td>"
                 f"<td>{f.get('finding','')}</td>"
                 f"<td>{_badge(f.get('severity','MEDIUM'))}</td>"
                 f"<td>{f.get('fix','')}</td></tr>")

    stack_html = ""
    if stack:
        cards = "".join(
            f'<div class="card" style="flex:0 0 auto;min-width:80px">'
            f'<div class="val" style="font-size:9pt">{v}</div>'
            f'<div class="lbl">{k}</div></div>'
            for k, v in stack.items()
        )
        stack_html = f'<div class="cards">{cards}</div>'

    return f"""
<div class="break"></div>
<h2>Technical SEO &nbsp; {_chip(score)}</h2>
{stack_html}
<table>
<tr><th>Category</th><th>Finding</th><th>Severity</th><th>Fix</th></tr>
{rows or '<tr><td colspan="4">No findings recorded.</td></tr>'}
</table>"""


def s_content(data: dict) -> str:
    content = data.get("content", {})
    score   = data.get("scores", {}).get("content", 0)
    eeat    = content.get("eeat", {})
    gaps    = content.get("gaps", [])

    eeat_rows = ""
    for dim in ("experience", "expertise", "authoritativeness", "trustworthiness"):
        d       = eeat.get(dim, {})
        s       = d.get("score", 0) if isinstance(d, dict) else 0
        finding = d.get("finding", "") if isinstance(d, dict) else str(d)
        eeat_rows += f"<tr><td><strong>{dim.capitalize()}</strong></td><td>{_chip(s)}</td><td>{finding}</td></tr>"

    gaps_html = ""
    for g in gaps:
        title  = g.get("title",  g) if isinstance(g, dict) else str(g)
        detail = g.get("detail", "")if isinstance(g, dict) else ""
        prio   = g.get("priority","high") if isinstance(g, dict) else "high"
        cls    = "issue" + (" medium" if prio == "medium" else "")
        gaps_html += f'<div class="{cls}"><strong>{title}</strong>'
        if detail:
            gaps_html += f'<p style="font-size:8pt;margin-top:3px">{detail}</p>'
        gaps_html += "</div>"

    return f"""
<div class="break"></div>
<h2>Content Quality & E-E-A-T &nbsp; {_chip(score)}</h2>
<table>
<tr><th>E-E-A-T Dimension</th><th>Score</th><th>Key Finding</th></tr>
{eeat_rows or '<tr><td colspan="3">No E-E-A-T data recorded.</td></tr>'}
</table>
{("<h3>Content Gaps — High Priority</h3>" + gaps_html) if gaps_html else ""}"""


def s_on_page(data: dict) -> str:
    on_page = data.get("on_page", {})
    score   = data.get("scores", {}).get("on_page", 0)
    pages   = on_page.get("pages", [])

    rows = ""
    for p in pages:
        tc = p.get("title_chars", "")
        h1 = p.get("h1_count", "")
        if isinstance(tc, int):
            tc_html = (f'<span style="color:{BRAND["danger"]}">{tc} — TOO SHORT</span>'
                       if tc < 30 else f"{tc} ✓" if tc <= 60 else str(tc))
        else:
            tc_html = str(tc)
        h1_html = (f'<span style="color:{BRAND["danger"]}">{h1} ✗</span>'
                   if isinstance(h1, int) and h1 != 1 else f"{h1} ✓")
        rows += (f"<tr><td>{p.get('page','')}</td><td>{tc_html}</td>"
                 f"<td>{p.get('meta_description','')}</td>"
                 f"<td>{h1_html}</td><td>{p.get('issues','')}</td></tr>")

    return f"""
<h2 style="margin-top:16px">On-Page SEO &nbsp; {_chip(score)}</h2>
<table>
<tr><th>Page</th><th>Title (chars)</th><th>Meta Description</th><th>H1</th><th>Issues</th></tr>
{rows or '<tr><td colspan="5">No page data recorded.</td></tr>'}
</table>"""


def s_schema(data: dict) -> str:
    schema  = data.get("schema", {})
    score   = data.get("scores", {}).get("schema", 0)
    present = schema.get("present", [])
    missing = schema.get("missing", [])
    errors  = schema.get("errors", [])

    miss_html = "".join(f'<div class="issue"><strong>{m}</strong></div>' for m in missing)
    err_html  = "".join(f'<div class="issue medium"><strong>{e}</strong></div>' for e in errors)

    return f"""
<h2>Schema / Structured Data &nbsp; {_chip(score)}</h2>
<p><strong>Detected types:</strong> {", ".join(present) if present else "None detected"}</p>
{("<h3>Missing Schema</h3>" + miss_html) if miss_html else ""}
{("<h3>Validation Errors</h3>" + err_html) if err_html else ""}"""


def s_performance(data: dict, chart_dir: Path) -> str:
    perf  = data.get("performance", {})
    score = data.get("scores", {}).get("performance", 0)
    lh    = perf.get("lighthouse", {})
    crux  = perf.get("crux", {})

    lh_html = ""
    if lh:
        cards = "".join(
            f'<div class="card"><div class="val" style="color:{_score_color(lh.get(k,0))}">'
            f'{lh.get(k,0)}</div><div class="lbl">{label}</div></div>'
            for label, k in [("Performance","performance"),("Accessibility","accessibility"),
                              ("Best Practices","best_practices"),("SEO","seo")]
        )
        lh_html = f'<h3>Lighthouse Scores</h3><div class="cards">{cards}</div>'

    crux_html = ""
    if crux:
        cwv_chart = chart_cwv_bars(crux, chart_dir)
        rows = ""
        for m in ("LCP", "INP", "CLS", "FCP", "TTFB"):
            d = crux.get(m, {})
            if not d:
                continue
            color = _rating_color(d.get("rating", ""))
            rows += (f'<tr><td>{m}</td><td>{d.get("p75","")}</td>'
                     f'<td style="color:{color};font-weight:bold">{d.get("rating","")}</td>'
                     f'<td>{d.get("good_pct","")}%</td>'
                     f'<td>{d.get("ni_pct","")}%</td>'
                     f'<td>{d.get("poor_pct","")}%</td></tr>')
        crux_html = f"""
<h3>CrUX Field Data (28-day Rolling Average)</h3>
{_img(cwv_chart,"CWV distribution") if cwv_chart else ""}
<table>
<tr><th>Metric</th><th>p75</th><th>Rating</th><th>Good %</th><th>NI %</th><th>Poor %</th></tr>
{rows or '<tr><td colspan="6">No CrUX data available.</td></tr>'}
</table>"""

    failed      = perf.get("failed_audits", [])
    failed_html = ""
    for f in failed:
        title  = f.get("title",  f) if isinstance(f, dict) else str(f)
        sc_val = f.get("score",  "") if isinstance(f, dict) else ""
        detail = f.get("detail", "") if isinstance(f, dict) else ""
        failed_html += f'<div class="issue medium"><strong>{title}</strong>'
        if sc_val != "":
            failed_html += f' <em style="color:{BRAND["danger"]}">(score: {int(float(sc_val)*100)}%)</em>'
        if detail:
            failed_html += f'<p style="font-size:8pt;margin-top:3px">{detail}</p>'
        failed_html += "</div>"

    return f"""
<div class="break"></div>
<h2>Performance & Core Web Vitals &nbsp; {_chip(score)}</h2>
{lh_html}
{crux_html}
{("<h3>Failed Audits</h3>" + failed_html) if failed_html else ""}"""


def s_geo(data: dict) -> str:
    geo       = data.get("geo", {})
    score     = data.get("scores", {}).get("geo", 0)
    platforms = geo.get("platforms", {})
    findings  = geo.get("findings", [])

    plat_rows = ""
    for platform, d in platforms.items():
        s    = d.get("score", 0) if isinstance(d, dict) else 0
        note = d.get("bottleneck", "") if isinstance(d, dict) else str(d)
        plat_rows += f"<tr><td>{platform}</td><td>{_chip(s)}</td><td>{note}</td></tr>"

    find_html = "".join(
        f'<div class="issue medium"><strong>'
        f'{f.get("text", f) if isinstance(f, dict) else str(f)}'
        f'</strong></div>'
        for f in findings
    )

    return f"""
<h2>AI Search Readiness (GEO) &nbsp; {_chip(score)}</h2>
{f'<table><tr><th>Platform</th><th>Score</th><th>Key Bottleneck</th></tr>{plat_rows}</table>' if plat_rows else ""}
{("<h3>Findings</h3>" + find_html) if find_html else ""}"""


def s_images(data: dict) -> str:
    images   = data.get("images", {})
    score    = data.get("scores", {}).get("images", 0)
    findings = images.get("findings", [])

    html = f'<h2>Images &nbsp; {_chip(score)}</h2>'
    for f in findings:
        title  = f.get("title",  f) if isinstance(f, dict) else str(f)
        detail = f.get("detail", "") if isinstance(f, dict) else ""
        sev    = f.get("severity","medium").lower()
        cls    = "issue" + (" high" if sev == "high" else " medium")
        html  += f'<div class="{cls}"><strong>{title}</strong>'
        if detail:
            html += f'<p style="font-size:8pt;margin-top:3px">{detail}</p>'
        html += "</div>"
    if not findings:
        html += "<p>No significant image issues found.</p>"
    return html


def s_backlinks(data: dict) -> str:
    bl = data.get("backlinks", {})
    if not bl:
        return ""
    score = data.get("scores", {}).get("backlinks")
    chip  = f" &nbsp; {_chip(score)}" if score is not None else ""

    cards = "".join(
        f'<div class="card"><div class="val">{bl.get(k,"")}</div><div class="lbl">{label}</div></div>'
        for label, k in [("Domain Authority","domain_authority"),
                          ("Referring Domains","referring_domains"),
                          ("Total Backlinks","total_backlinks")]
        if bl.get(k)
    )
    finds = "".join(
        f'<div class="issue medium"><strong>'
        f'{f.get("text",f) if isinstance(f,dict) else str(f)}'
        f'</strong></div>'
        for f in bl.get("findings", [])
    )

    return f"""
<h2>Backlink Profile{chip}</h2>
{f'<div class="cards">{cards}</div>' if cards else ""}
{finds}"""


def s_action_plan(data: dict) -> str:
    plan = data.get("action_plan", [])
    html = '<div class="break"></div><h2>Prioritised Action Plan</h2>'
    if not plan:
        return html + "<p>No action items recorded.</p>"

    by_prio: dict = {}
    for item in plan:
        p = (item.get("priority","MEDIUM").upper() if isinstance(item, dict) else "MEDIUM")
        by_prio.setdefault(p, []).append(item)

    for prio in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        items = by_prio.get(prio, [])
        if not items:
            continue
        html += f"<h3>{prio}</h3>"
        for item in items:
            title  = item.get("title",  item) if isinstance(item, dict) else str(item)
            detail = item.get("detail", "")   if isinstance(item, dict) else ""
            effort = item.get("effort", "")   if isinstance(item, dict) else ""
            impact = item.get("impact", "")   if isinstance(item, dict) else ""
            cls = ("issue" if prio == "CRITICAL"
                   else "issue high" if prio == "HIGH"
                   else "issue medium")
            html += f'<div class="{cls}"><strong>{title}</strong>'
            if effort or impact:
                html += f' <em style="color:{BRAND["muted"]};font-size:8pt">— Effort: {effort} | Impact: {impact}</em>'
            if detail:
                html += f'<p style="font-size:8pt;margin-top:3px">{detail}</p>'
            html += "</div>"
    return html


def s_roadmap(data: dict) -> str:
    roadmap = data.get("roadmap", [])
    html = '<div class="break"></div><h2>Implementation Roadmap</h2>'
    if roadmap:
        rows = "".join(
            f'<tr><td><strong>{p.get("phase","")}</strong></td>'
            f'<td>{p.get("timeframe","")}</td>'
            f'<td>{p.get("actions","")}</td>'
            f'<td>{p.get("impact","")}</td></tr>'
            for p in roadmap
        )
    else:
        rows = """
<tr><td><strong>Phase 1</strong></td><td>Week 1</td><td>Fix all Critical issues</td><td>Indexability, security baseline</td></tr>
<tr><td><strong>Phase 2</strong></td><td>Weeks 2–4</td><td>Address High priority items</td><td>Rankings improvement</td></tr>
<tr><td><strong>Phase 3</strong></td><td>Month 2</td><td>Medium priority optimisations</td><td>Content & authority gains</td></tr>
<tr><td><strong>Phase 4</strong></td><td>Ongoing</td><td>Low priority & monitoring</td><td>Sustained performance</td></tr>"""
    return html + f'<table><tr><th>Phase</th><th>Timeframe</th><th>Actions</th><th>Expected Impact</th></tr>{rows}</table>'


def s_footer(data: dict) -> str:
    domain = data.get("domain", "")
    date   = data.get("date", datetime.now().strftime("%d %B %Y"))
    return f'<div class="footer">Produced by Paresh M Patel · {domain} · {date}</div>'


# ─── Report assembly ─────────────────────────────────────────────────────────

def generate(data: dict, output_dir: str = ".") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    charts = out / "charts"
    charts.mkdir(exist_ok=True)

    body = "\n".join([
        s_cover(data, charts),
        s_toc(data),
        '<div class="break"></div>',
        s_executive(data, charts),
        s_technical(data),
        s_content(data),
        s_on_page(data),
        s_schema(data),
        s_performance(data, charts),
        s_geo(data),
        s_images(data),
        s_backlinks(data),
        s_action_plan(data),
        s_roadmap(data),
        s_footer(data),
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{_css()}</style></head>
<body>{body}</body>
</html>"""

    domain   = (data.get("domain","site")
                .replace("https://","").replace("http://","")
                .replace("www.","").replace(".","-"))
    datestamp = datetime.now().strftime("%Y-%m-%d")
    pdf_path  = out / f"SEO-Full-Audit-{domain}-{datestamp}.pdf"
    html_path = out / f"SEO-Full-Audit-{domain}-{datestamp}.html"

    html_path.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(out)).write_pdf(str(pdf_path))

    return {"pdf": str(pdf_path), "html": str(html_path)}


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified SEO Audit Report Generator")
    parser.add_argument("--data", "-d", help="JSON audit data file (or pipe via stdin)")
    parser.add_argument("--domain", required=True, help="Domain name")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory")
    parser.add_argument("--json", "-j", action="store_true", help="Output file paths as JSON")
    args = parser.parse_args()

    if args.data:
        with open(args.data) as f:
            data = json.load(f)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --data file or pipe JSON via stdin.", file=sys.stderr)
        sys.exit(1)

    data.setdefault("domain", args.domain)

    result = generate(data, args.output_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result.items():
            print(f"Generated ({k}): {v}")


if __name__ == "__main__":
    main()
