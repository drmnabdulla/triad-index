import os

ROOT = os.path.dirname(os.path.abspath(__file__))

AUTHOR_NAME = "Mostafa Abdulla, PhD"
AUTHOR_EMAIL = "mnabdull@ieee.org"
SITE_URL = "https://drmnabdulla.github.io/triad-index"

CHAPTERS = [
    {"slug": "index", "file": "index.html", "num": "00", "nav": "Overview"},
    {"slug": "background", "file": "background.html", "num": "01", "nav": "Background & Objectives"},
    {"slug": "methodology", "file": "methodology.html", "num": "02", "nav": "The Scoring Methodology"},
    {"slug": "case-studies", "file": "case-studies.html", "num": "03", "nav": "Case Studies"},
    {"slug": "calculator", "file": "calculator.html", "num": "04", "nav": "Live Calculator"},
    {"slug": "tool", "file": "tool.html", "num": "05", "nav": "Desktop GUI Tool"},
    {"slug": "appendix", "file": "appendix.html", "num": "06", "nav": "Appendix: Full Levels"},
    {"slug": "advisory", "file": "advisory.html", "num": "07", "nav": "Advisory & Contact"},
]

def sidebar_html(active_slug):
    items = []
    for c in CHAPTERS:
        cls = "chapter active" if c["slug"] == active_slug else "chapter"
        items.append(f'<a class="{cls}" href="{c["file"]}"><span class="n">{c["num"]}</span>{c["nav"]}</a>')
    return "\n        ".join(items)

def page_nav(active_slug):
    idx = next(i for i, c in enumerate(CHAPTERS) if c["slug"] == active_slug)
    prev_html = ""
    next_html = ""
    if idx > 0:
        p = CHAPTERS[idx - 1]
        prev_html = f'<a href="{p["file"]}"><span class="dir">&larr; Previous</span>{p["nav"]}</a>'
    else:
        prev_html = "<span></span>"
    if idx < len(CHAPTERS) - 1:
        n = CHAPTERS[idx + 1]
        next_html = f'<a class="next" href="{n["file"]}"><span class="dir">Next &rarr;</span>{n["nav"]}</a>'
    else:
        next_html = "<span></span>"
    return prev_html, next_html

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} — TRIAD Index</title>
<meta name="description" content="{description}" />
<meta name="author" content="{author}" />
<meta property="og:type" content="website" />
<meta property="og:title" content="{title} — TRIAD Index" />
<meta property="og:description" content="{description}" />
<meta property="og:url" content="{og_url}" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{title} — TRIAD Index" />
<meta name="twitter:description" content="{description}" />
<link rel="stylesheet" href="assets/book.css" />
</head>
<body>
<button class="nav-toggle" id="nav-toggle">MENU</button>
<div class="page">
  <aside class="sidebar" id="sidebar">
    <div class="sidebar__brand">
      <span class="sidebar__mark">△</span> TRIAD Index
    </div>
    <nav>
        {sidebar}
    </nav>
    <div class="sidebar__download">
      <p>Prefer a desktop tool? Download the full-featured GUI version.</p>
      <a class="btn btn--primary" href="downloads/trl-readiness-gui.zip">Download GUI (.zip)</a>
    </div>
  </aside>
  <main class="content">
    <article>
      <div class="breadcrumb">CHAPTER {num}</div>
      {body}
      <div class="page-nav">
        {prev_link}
        {next_link}
      </div>
    </article>
  </main>
</div>
<script src="assets/site.js"></script>
{extra_scripts}
</body>
</html>
"""

def render(slug, title, description, body, extra_scripts=""):
    c = next(c for c in CHAPTERS if c["slug"] == slug)
    prev_link, next_link = page_nav(slug)
    html = TEMPLATE.format(
        title=title,
        description=description,
        author=AUTHOR_NAME,
        og_url=f"{SITE_URL}/{c['file']}",
        sidebar=sidebar_html(slug),
        num=c["num"],
        body=body,
        prev_link=prev_link,
        next_link=next_link,
        extra_scripts=extra_scripts,
    )
    with open(os.path.join(ROOT, c["file"]), "w") as f:
        f.write(html)

# ---------------------------------------------------------------------------
# CHAPTER 00 — Overview
# ---------------------------------------------------------------------------
render(
    "index",
    "Overview",
    "A gate-based methodology and free live calculator that scores ventures on Technology, "
    "Manufacturing, and Commercial Readiness (TRL/MRL/CRL) — built for founders preparing for "
    "diligence and investors screening technical deals.",
    f"""
      <h1>The TRIAD Index</h1>
      <p class="subtitle">A gate-based methodology for assessing Technology, Manufacturing, and Commercial
      Readiness — built for founders preparing for diligence, and investors screening deep-tech and hardware deals.</p>
      <p style="font-family: var(--mono); font-size: 0.82rem; color: var(--ink-faint); margin-top: -20px;">
        By {AUTHOR_NAME} &middot; <a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a>
      </p>

      <p>Emerging and growing companies often struggle to answer a deceptively simple question: <strong>how ready
      is this, really?</strong> Technical readiness, manufacturing readiness, and commercial readiness usually get
      assessed separately, if at all — which leaves gaps invisible until diligence surfaces them the hard way.</p>

      <p>This book documents a methodology that integrates three established frameworks — Technology Readiness
      Level (TRL), Manufacturing Readiness Level (MRL), and Commercial Readiness Level (CRL) — into one
      cohesive, gate-based scoring tool, adapted for use across industries rather than a single domain.</p>

      <div class="callout">
        <p><strong>What's in this book:</strong> the background and objectives behind the methodology, exactly how
        the gate-based scoring works (with the real logic, not just a description), three worked case studies,
        a live in-browser calculator, and a downloadable desktop GUI implementing the same engine.</p>
      </div>

      <h2>Who this is for</h2>
      <ul>
        <li><strong>Startups &amp; SMEs</strong> — identify readiness gaps and prepare for scaling or fundraising.</li>
        <li><strong>Investors &amp; stakeholders</strong> — evaluate the potential and risk of a technical deal with a
        structured, repeatable read rather than a pitch deck alone.</li>
        <li><strong>R&amp;D teams</strong> — align technical progress with manufacturing and commercial objectives.</li>
      </ul>

      <div class="download-hero">
        <a class="btn btn--primary" href="calculator.html">Run the live calculator &rarr;</a>
        <a class="btn btn--ghost" href="methodology.html">Read the methodology</a>
      </div>
    """,
)

# ---------------------------------------------------------------------------
# CHAPTER 01 — Background & Objectives
# ---------------------------------------------------------------------------
render(
    "background",
    "Background & Objectives",
    "Where readiness-level frameworks come from, and what this methodology sets out to do.",
    """
      <h1>Background &amp; Objectives</h1>

      <h2>Background</h2>
      <p>The concept of readiness levels originated at NASA, which developed the Technology Readiness Level (TRL)
      framework to assess how mature a technology was for spaceflight. Over time, complementary frameworks —
      Manufacturing Readiness Level (MRL) from the U.S. Department of Defense, and various Commercial Readiness
      Level (CRL) indices from the clean-energy sector — were introduced to address the broader arc of product
      development and commercialization.</p>
      <p>Each of these frameworks has proven effective within its own domain. But used separately, they leave
      blind spots: a technically brilliant product can still fail commercially, and a commercially validated idea
      can stall on manufacturing it hasn't yet solved. Their potential for cross-industry, integrated use
      motivated the development of a single, more versatile tool.</p>

      <h2>Objectives</h2>
      <ol>
        <li><strong>Provide a comprehensive evaluation.</strong> Address technical, manufacturing, and commercial
        readiness in one unified framework, rather than three disconnected assessments.</li>
        <li><strong>Facilitate decision-making.</strong> Enable companies to identify gaps and prioritize effort
        for advancing their innovations — not just score them.</li>
        <li><strong>Enhance cross-industry applicability.</strong> Adapt the TRL/MRL/CRL frameworks for use across
        diverse industries and organizational contexts, from agri-hardware to pure software.</li>
      </ol>

      <div class="callout callout--good">
        <p>The chapters that follow walk through exactly how these objectives were implemented — including the
        gate-based scoring logic in <a href="methodology.html">Chapter 02</a>, and how it plays out differently
        across a hardware, IoT, and software venture in <a href="case-studies.html">Chapter 03</a>.</p>
      </div>
    """,
)

# ---------------------------------------------------------------------------
# CHAPTER 02 — Methodology
# ---------------------------------------------------------------------------
render(
    "methodology",
    "The Scoring Methodology",
    "How the gate-based TRL/MRL/CRL scoring engine actually works, with the real logic.",
    """
      <h1>The Scoring Methodology</h1>
      <p class="subtitle">Three frameworks, ten categories, and one gating rule that ties them together.</p>

      <h2>The three axes</h2>
      <table>
        <thead><tr><th>Axis</th><th>Tracks</th><th>Range</th></tr></thead>
        <tbody>
          <tr><td><span class="lvl-badge">TRL</span></td><td>The underlying science and engineering — from basic
          principles observed to a system proven under full operating conditions.</td><td>1 – 9</td></tr>
          <tr><td><span class="lvl-badge">MRL</span></td><td>The ability to produce the technology reliably —
          process development, pilot production, scale-up to full-rate manufacturing.</td><td>1 – 10</td></tr>
          <tr><td><span class="lvl-badge">CRL</span></td><td>Market and business maturity — product definition,
          competitive positioning, team, go-to-market, supply chain, and financing.</td><td>1 – 9</td></tr>
        </tbody>
      </table>

      <h2>Ten sub-categories</h2>
      <p>Each axis is broken into sub-categories, each with its own concrete, evidence-based level descriptions
      (the full text for every level is in the <a href="appendix.html">Appendix</a> and in the live calculator):</p>
      <table>
        <thead><tr><th>Category</th><th>Feeds into</th><th>Levels</th></tr></thead>
        <tbody>
          <tr><td>Technology</td><td>TRL</td><td>1–5</td></tr>
          <tr><td>Product Development</td><td>TRL</td><td>1–5</td></tr>
          <tr><td>Manufacturing Research</td><td>MRL</td><td>1–5</td></tr>
          <tr><td>Manufacturing Scale-up</td><td>MRL</td><td>1–6</td></tr>
          <tr><td>Product Definition/Design</td><td>CRL</td><td>1–6</td></tr>
          <tr><td>Competitive Landscape</td><td>CRL</td><td>1–5</td></tr>
          <tr><td>Team</td><td>CRL</td><td>1–5</td></tr>
          <tr><td>Go-To-Market</td><td>CRL</td><td>1–6</td></tr>
          <tr><td>Supply Chain</td><td>CRL</td><td>1–6</td></tr>
          <tr><td>Finance</td><td>CRL</td><td>1–7</td></tr>
        </tbody>
      </table>

      <h2>The gate rule — not an average</h2>
      <p>This is the part that makes the methodology work in practice rather than just on paper: a venture's
      overall score on each axis is <strong>not an average</strong> of its category levels. It's a gate. The
      scorer walks up the scale and assigns the <strong>highest level whose entire set of category minimums is
      satisfied</strong>. A venture can't reach CRL 6 by being excellent at Team while weak on Finance — every
      category required for that level has to clear its bar first.</p>

      <p>Here is the actual scoring function, unchanged from the underlying engine:</p>
      <pre><code>function scoreFromRules(selections, rules) {
  let best = 0;
  Object.keys(rules).map(Number).sort((a, b) => a - b).forEach((level) => {
    const req = rules[level];
    const met = Object.entries(req).every(
      ([cat, min]) => (selections[cat] || 0) >= min
    );
    if (met) best = level;
  });
  return best;
}</code></pre>

      <p>And a fragment of the actual gate table for CRL — notice how the requirement tightens across six
      categories simultaneously as the level rises:</p>
      <pre><code>const CRL_RULES = {
  1: { "Product Definition/Design": 1, "Competitive Landscape": 1, "Team": 1,
       "Go-To-Market": 1, "Supply Chain": 1, "Finance": 1 },
  4: { "Product Definition/Design": 4, "Competitive Landscape": 4, "Team": 3,
       "Go-To-Market": 3, "Supply Chain": 2, "Finance": 2 },
  9: { "Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 5,
       "Go-To-Market": 6, "Supply Chain": 6, "Finance": 7 },
  // ...levels 2, 3, 5, 6, 7, 8 fill the gaps between these
};</code></pre>

      <h2>Customization</h2>
      <p>Because the framework is gate-based per category, it can be customized without redesigning the whole
      tool: categories that don't apply to a given industry (Manufacturing Research and Scale-up have limited
      relevance to pure software, for instance — see <a href="case-studies.html">the AI power-saving case
      study</a>) can be down-weighted or excluded from that axis's gate entirely.</p>

      <div class="callout">
        <p>Want to see this scored live against your own venture? Jump to the
        <a href="calculator.html">interactive calculator</a> — it runs this exact engine in the browser.</p>
      </div>
    """,
)

# ---------------------------------------------------------------------------
# CHAPTER 03 — Case Studies
# ---------------------------------------------------------------------------
render(
    "case-studies",
    "Case Studies",
    "Three ventures, three different readiness profiles, scored with the same methodology.",
    """
      <h1>Case Studies</h1>
      <p class="subtitle">Illustrative scores — not audited figures — showing how the same framework surfaces
      different bottlenecks depending on what kind of venture it's applied to.</p>
      <div class="card-grid" id="case-grid"></div>
      <div class="callout">
        <p>Each card's <strong>Load into calculator</strong> button pushes these exact category scores into the
        <a href="calculator.html">live calculator</a> so you can see the full gap analysis, radar chart, and
        benchmark comparison for that venture.</p>
      </div>
    """,
    extra_scripts='<script src="assets/data.js"></script>\n<script src="assets/app.js"></script>',
)

# ---------------------------------------------------------------------------
# CHAPTER 04 — Live Calculator
# ---------------------------------------------------------------------------
render(
    "calculator",
    "Live Calculator",
    "Run your own TRL/MRL/CRL readiness assessment in the browser.",
    """
      <h1>Live Calculator</h1>
      <p class="subtitle">Move each slider to the level whose description best matches where the venture
      actually is today. Scores update live using the exact gate logic described in
      <a href="methodology.html">Chapter 02</a>.</p>

      <div class="calc-layout">
        <div id="sliders"></div>
        <aside class="results-panel">
          <h3>Current Readiness</h3>
          <div class="gauges" id="gauges"></div>
          <div class="radar-wrap">
            <h3>Category Maturity</h3>
            <canvas id="radar-canvas" width="340" height="280"></canvas>
          </div>
          <div class="results-block">
            <h3>Next Gate to Clear</h3>
            <div id="next-steps"></div>
          </div>
          <div class="results-block critical-gaps">
            <h3>Highest-Impact Gaps</h3>
            <div id="critical-gaps"></div>
          </div>
          <div class="results-block">
            <h3>Benchmark vs. Stage</h3>
            <table class="benchmark-table">
              <thead><tr><th>Stage</th><th>TRL</th><th>MRL</th><th>CRL</th><th>&Delta; vs you</th></tr></thead>
              <tbody id="benchmark-body"></tbody>
            </table>
          </div>
        </aside>
      </div>
    """,
    extra_scripts='<script src="assets/chart.umd.min.js"></script>\n<script src="assets/data.js"></script>\n<script src="assets/app.js"></script>',
)

# ---------------------------------------------------------------------------
# CHAPTER 05 — Desktop GUI Tool
# ---------------------------------------------------------------------------
render(
    "tool",
    "Desktop GUI Tool",
    "A standalone Python/Tkinter desktop application implementing the same scoring engine.",
    """
      <h1>Desktop GUI Tool</h1>
      <p class="subtitle">The same gate-based scoring engine, packaged as a standalone Python desktop application
      for offline assessments, project management, and formal report export.</p>

      <div class="download-hero">
        <a class="btn btn--primary" href="downloads/trl-readiness-gui.zip">Download (.zip)</a>
        <a class="btn btn--ghost" href="downloads/trl_readiness_gui.py">Download source only (.py)</a>
      </div>

      <h2>What it does</h2>
      <ul>
        <li>Walks through all ten readiness categories with the same descriptions used in the web calculator.</li>
        <li>Live TRL / MRL / CRL scoring with the identical gate logic — an assessment done here is directly
        comparable to one done in the browser.</li>
        <li>Dashboard tab: category maturity heatmap, a progress timeline, and stage benchmarks.</li>
        <li>Recommendations tab: critical-gap ranking (weighted by impact) and an auto-generated roadmap.</li>
        <li>Save and reload assessments as JSON; export to CSV, Excel, or a formatted PDF report.</li>
        <li>Local, SQLite-backed project manager for tracking multiple ventures or repeat assessments over time.</li>
      </ul>

      <h2>Requirements</h2>
      <p>Python 3.9+ with Tkinter (included in most Python installs). Everything else is optional — the app
      detects what's installed and simply disables the related export or chart features if a library is missing:</p>
      <pre><code>pip install matplotlib numpy pandas openpyxl reportlab</code></pre>

      <h2>Run it</h2>
      <pre><code>python3 trl_readiness_gui.py</code></pre>

      <div class="callout callout--good">
        <p>The web calculator and this desktop tool share one scoring engine, so you can start an assessment on
        a laptop offline and cross-check it against the browser version — the numbers will match exactly.</p>
      </div>
    """,
)

# ---------------------------------------------------------------------------
# CHAPTER 06 — Appendix
# ---------------------------------------------------------------------------
def level_table(rows):
    body = "".join(f"<tr><td><span class='lvl-badge'>{i+1}</span></td><td>{r}</td></tr>" for i, r in enumerate(rows))
    return f"<table><thead><tr><th>Level</th><th>Definition</th></tr></thead><tbody>{body}</tbody></table>"

trl_rows = [
    "Basic principles observed and reported",
    "Technology concept and/or application formulated",
    "Analytical and experimental critical function and/or characteristic proof of concept",
    "Component and/or breadboard validation in a laboratory environment",
    "Component and/or breadboard validation in a relevant environment",
    "System/subsystem model or prototype demonstration in a relevant environment",
    "System prototype demonstration in an operational environment",
    "Actual system completed and qualified through test and demonstration",
    "Actual system proven through successful mission operations",
]
mrl_rows = [
    "Basic manufacturing implications identified",
    "Manufacturing concepts identified",
    "Manufacturing proof of concept developed",
    "Capability to produce the technology in a laboratory environment",
    "Capability to produce prototype components in a production-relevant environment",
    "Capability to produce a prototype system or subsystem in a production-relevant environment",
    "Capability to produce systems, subsystems, or components in a production-representative environment",
    "Pilot line capability demonstrated; ready to begin low-rate initial production",
    "Low-rate production demonstrated; capability in place to begin full-rate production",
    "Full-rate production demonstrated; lean production practices in place",
]
crl_rows = [
    "Market and business opportunity identified",
    "Value proposition and target market validated",
    "Initial market engagement and feedback obtained",
    "Commercial scale-up initiated",
    "Early adopters secured",
    "Established market presence with repeat customers",
    "Broad market adoption and customer satisfaction demonstrated",
    "Product/service optimization and differentiation achieved",
    "Full market penetration and industry leadership attained",
]

render(
    "appendix",
    "Appendix: Full Level Definitions",
    "The complete TRL, MRL, and CRL scale definitions, plus references.",
    f"""
      <h1>Appendix: Full Level Definitions</h1>
      <p class="subtitle">The standard top-level scale definitions behind each axis. The ten sub-category
      descriptions actually used for scoring are in the <a href="calculator.html">live calculator</a>.</p>

      <h2>Technology Readiness Level (TRL)</h2>
      {level_table(trl_rows)}

      <h2>Manufacturing Readiness Level (MRL)</h2>
      {level_table(mrl_rows)}

      <h2>Commercial Readiness Level (CRL)</h2>
      {level_table(crl_rows)}

      <h2>References</h2>
      <ul>
        <li>NASA Technology Readiness Levels Handbook</li>
        <li>Manufacturing Readiness Level Guidelines, U.S. Department of Defense</li>
        <li>Commercial Readiness Index for Clean Energy Innovations</li>
      </ul>

      <h2>Recommendations for continued development</h2>
      <ol>
        <li><strong>Industry collaboration</strong> — engage with industry partners to refine criteria and benchmarks.</li>
        <li><strong>Training and workshops</strong> — equip users with the skills to implement the tool effectively.</li>
        <li><strong>Continuous improvement</strong> — incorporate user feedback and emerging trends to enhance the framework.</li>
      </ol>
    """,
)

# ---------------------------------------------------------------------------
# CHAPTER 07 — Advisory & Contact
# ---------------------------------------------------------------------------
render(
    "advisory",
    "Advisory & Contact",
    "Readiness diligence services for founders and investors.",
    f"""
      <h1>Advisory &amp; Contact</h1>
      <p class="subtitle">I use the TRIAD Index to give technical founders a clear-eyed view of where their
      venture actually stands, and to give investors a structured, repeatable way to compare deep-tech and
      hardware deals on more than a pitch deck.</p>

      <h2>Services</h2>
      <table>
        <thead><tr><th>Service</th><th>What it delivers</th></tr></thead>
        <tbody>
          <tr><td><strong>Readiness Audit</strong></td><td>A full TRL/MRL/CRL scoring pass with evidence review,
          benchmarked against stage-appropriate peers.</td></tr>
          <tr><td><strong>Investment Diligence Support</strong></td><td>An independent readiness read for
          investors evaluating a technical deal, delivered alongside the gap analysis.</td></tr>
          <tr><td><strong>Gap-Closing Roadmap</strong></td><td>A prioritized, category-by-category plan for what
          to fix first to move the needle on the next gate.</td></tr>
        </tbody>
      </table>

      <h2>Get in touch</h2>
      <div class="contact-card">
        <div class="contact-card__row"><span>NAME</span><span>{AUTHOR_NAME}</span></div>
        <div class="contact-card__row"><span>EMAIL</span><span>{AUTHOR_EMAIL}</span></div>
        <a href="mailto:{AUTHOR_EMAIL}" class="btn btn--primary">Book a readiness review</a>
      </div>
    """,
)

print("Built", len(CHAPTERS), "chapters.")
