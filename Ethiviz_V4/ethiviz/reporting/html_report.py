from __future__ import annotations
import json
from ethiviz.reporting.base import BiasReport

# ──────────────────────────────────────────────────────────────────────────────
# Helper — safe JSON serialisation for Jinja2 template injection
# ──────────────────────────────────────────────────────────────────────────────

def _safe_json(obj) -> str:
    return json.dumps(obj, default=str)


HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EthiViz Bias Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    :root {
      --primary: #6366f1;
      --secondary: #a855f7;
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.85);
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #22d3ee;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
      --border: rgba(255,255,255,0.08);
    }
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0; padding: 0;
      display: flex;
      min-height: 100vh;
    }
    /* ── Sidebar ──────────────────────────────────────────────────────── */
    .sidebar {
      width: 260px; flex-shrink: 0;
      background: rgba(10,18,35,0.98);
      border-right: 1px solid var(--border);
      padding: 2rem 1.5rem;
      display: flex; flex-direction: column; gap: 1.25rem;
      position: sticky; top: 0; height: 100vh;
      overflow-y: auto;
    }
    .sidebar-logo { display: flex; align-items: center; gap: .75rem; margin-bottom: .5rem; }
    .sidebar-logo .mark {
      width: 38px; height: 38px; border-radius: .5rem;
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 1.25rem; color: #fff;
    }
    .sidebar-logo h1 { font-size: 1.35rem; margin: 0; font-weight: 700; }
    .sidebar nav a {
      display: block; padding: .6rem .9rem; border-radius: .5rem;
      color: var(--muted); text-decoration: none; font-size: .875rem;
      transition: background .15s, color .15s;
    }
    .sidebar nav a:hover, .sidebar nav a.active {
      background: rgba(99,102,241,.15); color: var(--accent);
    }
    .sidebar-footer { margin-top: auto; font-size: .75rem; color: #475569; }
    .upload-area {
      border: 2px dashed rgba(99,102,241,.35); border-radius: .75rem;
      padding: 1rem; text-align: center; cursor: pointer;
      transition: border-color .2s;
    }
    .upload-area:hover, .upload-area.drag-over { border-color: var(--primary); background: rgba(99,102,241,.06); }
    /* Loading overlay */
    #loading-overlay {
      display: none; position: fixed; inset: 0; z-index: 9999;
      background: rgba(15,23,42,.85); backdrop-filter: blur(4px);
      flex-direction: column; align-items: center; justify-content: center;
      color: #e2e8f0; font-family: inherit;
    }
    #loading-overlay.visible { display: flex; }
    .spinner {
      width: 56px; height: 56px; border: 5px solid rgba(99,102,241,.25);
      border-top-color: var(--primary); border-radius: 50%;
      animation: spin 0.9s linear infinite; margin-bottom: 1.5rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #loading-msg { font-size: 1.1rem; font-weight: 600; margin-bottom: .5rem; }
    #loading-sub { font-size: .85rem; color: var(--muted); }
    .btn {
      width: 100%; padding: .75rem 1rem; border: none; border-radius: .5rem;
      font-weight: 600; font-size: .875rem; cursor: pointer;
      transition: opacity .2s;
    }
    .btn:hover { opacity: .85; }
    .btn-primary { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff; }
    .btn-danger { background: rgba(239,68,68,.15); color: var(--danger); border: 1px solid rgba(239,68,68,.25); }
    /* ── Main content ─────────────────────────────────────────────────── */
    .main { flex: 1; padding: 2rem 2.5rem; min-width: 0; }
    .page-title { font-size: 2rem; font-weight: 800; margin: 0 0 .25rem; }
    .page-sub { color: var(--muted); font-size: .9rem; margin-bottom: 2rem; }
    /* ── Cards ────────────────────────────────────────────────────────── */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 1rem; padding: 1.75rem;
      margin-bottom: 1.5rem;
      backdrop-filter: blur(8px);
    }
    .card h2 {
      margin: 0 0 1.25rem;
      font-size: 1rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; color: var(--accent);
      padding-bottom: .5rem; border-bottom: 1px solid var(--border);
    }
    /* ── KPI grid ─────────────────────────────────────────────────────── */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    @media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(2,1fr); } }
    .kpi {
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: .75rem; padding: 1.25rem;
      display: flex; flex-direction: column; gap: .35rem;
    }
    .kpi-label { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
    .kpi-value { font-size: 1.75rem; font-weight: 800; }
    .kpi-sub { font-size: .75rem; color: var(--muted); }
    /* ── Risk banner ──────────────────────────────────────────────────── */
    .risk-banner {
      padding: 1rem 1.5rem; border-radius: .75rem;
      font-weight: 700; font-size: .95rem;
      letter-spacing: .05em; text-transform: uppercase;
      margin-bottom: 1.5rem;
    }
    .risk-critical { background: rgba(239,68,68,.2); border: 1px solid rgba(239,68,68,.4); color: #fca5a5; }
    .risk-high { background: rgba(245,158,11,.2); border: 1px solid rgba(245,158,11,.4); color: #fcd34d; }
    .risk-medium { background: rgba(34,211,238,.15); border: 1px solid rgba(34,211,238,.3); color: #67e8f9; }
    .risk-low { background: rgba(16,185,129,.15); border: 1px solid rgba(16,185,129,.3); color: #6ee7b7; }
    /* ── Charts layout ────────────────────────────────────────────────── */
    .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    .charts-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    @media (max-width: 900px) { .charts-row, .charts-row-3 { grid-template-columns: 1fr; } }
    .chart-wrap { position: relative; height: 280px; }
    .chart-wrap canvas { max-height: 280px; }
    /* ── Heatmap ──────────────────────────────────────────────────────── */
    .heatmap-table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    .heatmap-table th { padding: .5rem .75rem; color: var(--muted); font-weight: 600;
      text-align: center; border-bottom: 1px solid var(--border); }
    .heatmap-table td { padding: .4rem .5rem; text-align: center; }
    .heatmap-table td.text-col {
      text-align: left; max-width: 340px;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      color: var(--text); padding-left: .75rem;
    }
    /* ── Tables ───────────────────────────────────────────────────────── */
    .data-table { width: 100%; border-collapse: collapse; font-size: .875rem; }
    .data-table th { color: var(--accent); text-align: left; padding: .75rem 1rem;
      border-bottom: 1px solid var(--border); font-weight: 600; font-size: .75rem; text-transform: uppercase; }
    .data-table td { padding: .75rem 1rem; border-bottom: 1px solid rgba(255,255,255,.04); }
    .data-table tr:last-child td { border-bottom: none; }
    /* ── Badges ───────────────────────────────────────────────────────── */
    .badge {
      display: inline-block; padding: .2rem .6rem; border-radius: 999px;
      font-size: .75rem; font-weight: 600;
    }
    .badge-red { background: rgba(239,68,68,.2); color: #fca5a5; }
    .badge-amber { background: rgba(245,158,11,.2); color: #fcd34d; }
    .badge-green { background: rgba(16,185,129,.2); color: #6ee7b7; }
    .badge-blue { background: rgba(34,211,238,.15); color: #67e8f9; }
    /* ── Token attribution ────────────────────────────────────────────── */
    .token-attr { font-family: 'Fira Code', monospace; font-size: .875rem;
      line-height: 2; padding: .75rem; background: rgba(0,0,0,.2);
      border-radius: .5rem; flex-wrap: wrap; display: flex; gap: .2rem; }
    .token { padding: .1rem .3rem; border-radius: .25rem; }
    /* ── CI bar (WEAT forest plot) ────────────────────────────────────── */
    .forest-row { display: flex; align-items: center; gap: .75rem;
      font-size: .8rem; padding: .5rem 0; border-bottom: 1px solid var(--border); }
    .forest-label { width: 220px; flex-shrink: 0; color: var(--text); }
    .forest-bar-wrap { flex: 1; position: relative; height: 20px; }
    .forest-null { position: absolute; top: 0; bottom: 0; width: 1px;
      background: rgba(255,255,255,.3); }
    .forest-ci { position: absolute; top: 8px; height: 4px;
      background: rgba(99,102,241,.4); border-radius: 2px; }
    .forest-point { position: absolute; top: 5px; width: 10px; height: 10px;
      border-radius: 50%; transform: translateX(-50%); }
    .forest-sig { background: var(--danger); }
    .forest-ns { background: var(--muted); }
    .forest-val { width: 60px; flex-shrink: 0; text-align: right; color: var(--muted); }
    /* ── Progress ─────────────────────────────────────────────────────── */
    .progress-bar-wrap { width: 100%; background: rgba(255,255,255,.08);
      border-radius: 999px; height: 8px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 999px;
      background: linear-gradient(90deg, var(--primary), var(--accent)); }
    /* ── Misc ─────────────────────────────────────────────────────────── */
    details summary { cursor: pointer; padding: .5rem; border-radius: .25rem;
      background: rgba(255,255,255,.03); user-select: none; }
    details[open] summary { color: var(--accent); }
    .ci-text { font-size: .75rem; color: var(--muted); }
    .synergy-pill { display: inline-block; margin: .25rem;
      background: rgba(168,85,247,.15); border: 1px solid rgba(168,85,247,.3);
      color: #d8b4fe; padding: .25rem .75rem; border-radius: 999px; font-size: .8rem; }
  </style>
</head>
<body>

<!-- ── Loading overlay ──────────────────────────────────────────── -->
<div id="loading-overlay">
  <div class="spinner"></div>
  <div id="loading-msg">Analysing…</div>
  <div id="loading-sub">Please wait</div>
</div>

<!-- ── Sidebar ──────────────────────────────────────────────────── -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <div class="mark">E</div>
    <h1>EthiViz</h1>
  </div>

  <nav>
    <a href="#summary" class="active">Summary</a>
    <a href="#lens-scores">Lens Scores</a>
    <a href="#heatmap">Text Heatmap</a>
    <a href="#weat">WEAT Analysis</a>
    <a href="#dimensions">Dimension Breakdown</a>
    <a href="#regulatory">Regulatory</a>
    <a href="#candidates">Flagged Texts</a>
    <a href="#provenance">Provenance</a>
  </nav>

  <!-- Text upload form — native submission replaces the page -->
  <form id="textForm" method="POST" action="/analyze/text"
        enctype="multipart/form-data" style="margin:0">
    <div class="upload-area" id="textDropZone"
         onclick="document.getElementById('textFile').click()">
      <div style="font-size:1.5rem;margin-bottom:.25rem">📄</div>
      <div style="font-size:.8rem;color:var(--muted)">Drop .txt/.csv/.json or click</div>
    </div>
    <input type="file" id="textFile" name="file" style="display:none"
           accept=".txt,.csv,.json,.xlsx">
  </form>

  <!-- Image upload form -->
  <form id="imageForm" method="POST" action="/analyze/image"
        enctype="multipart/form-data" style="margin:0">
    <button type="button" class="btn btn-primary"
            onclick="document.getElementById('imageFile').click()">
      + Analyse Image
    </button>
    <input type="file" id="imageFile" name="file" style="display:none"
           accept="image/*">
  </form>

  <!-- Last file info -->
  {% set fname = report.scored_result.metadata.get('filename','') %}
  {% set fsize = report.scored_result.metadata.get('file_size','') %}
  {% if fname %}
  <div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.2);
              border-radius:.5rem;padding:.6rem .75rem;font-size:.75rem;color:var(--muted);
              word-break:break-all;">
    <div style="color:var(--text);font-weight:600;margin-bottom:.2rem">Last analysed</div>
    <div>{{ fname }}</div>
    {% if fsize %}<div style="margin-top:.2rem">{{ fsize }}</div>{% endif %}
  </div>
  {% endif %}

  <button class="btn btn-danger" onclick="stopPlatform()">Stop Platform</button>

  <div class="sidebar-footer">
    EthiViz v4 &bull; IU University 2025<br>
    Analysis&nbsp;ID: {{ report.scored_result.reproducibility.analysis_id }}
  </div>
</aside>

<!-- ── Main ─────────────────────────────────────────────────────── -->
<main class="main">

  <p class="page-sub">
    {% set src = report.scored_result.metadata.get('source_type','text') %}
    {% set fname = report.scored_result.metadata.get('filename','') %}
    {% if fname %}<strong>{{ fname }}</strong> &bull; {% endif %}
    {{ report.scored_result.metadata.get('n_texts', '?') }} text{% if report.scored_result.metadata.get('n_texts',1)|int != 1 %}s{% endif %} &bull;
    Language: {{ report.scored_result.metadata.get('language_detected','en')|upper }} &bull;
    {{ report.scored_result.reproducibility.recorded_at[:10] }}
  </p>

  {% set src_content = report.scored_result.metadata.get('source_content','') %}
  {% set vision = report.scored_result.metadata.get('vision_findings','') %}
  {% set vision_detail = report.scored_result.metadata.get('vision_detail', {}) %}
  {% if src_content and src_content.startswith('data:image') %}
  <div class="card" style="display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap">
    <img src="{{ src_content }}" alt="Uploaded image"
         style="max-width:280px;max-height:280px;border-radius:.5rem;
                border:1px solid var(--border);object-fit:contain;flex-shrink:0">
    <div style="flex:1;min-width:200px">
      <div class="section-title" style="margin-bottom:.75rem">Vision Analysis</div>
      {% if vision %}
      <p style="font-size:.9rem;color:var(--text);margin-bottom:.75rem">{{ vision }}</p>
      {% endif %}
      {% if vision_detail %}
      <table style="width:100%;font-size:.8rem;border-collapse:collapse">
        {% for k,v in vision_detail.items() %}
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:.3rem .5rem .3rem 0;color:var(--muted);white-space:nowrap">
            {{ k.replace('_',' ').title() }}</td>
          <td style="padding:.3rem 0;color:var(--text)">{{ v }}</td>
        </tr>
        {% endfor %}
      </table>
      {% endif %}
    </div>
  </div>
  {% endif %}

  <!-- KPI row -->
  <div class="kpi-grid">
    <div class="kpi">
      <span class="kpi-label">Consensus Bias Score</span>
      <span class="kpi-value" style="color:
        {%- if report.scored_result.consensus_score > 0.6 %}var(--danger)
        {%- elif report.scored_result.consensus_score > 0.35 %}var(--warning)
        {%- else %}var(--success){% endif %}">
        {{ "%.3f"|format(report.scored_result.consensus_score or 0) }}
      </span>
      <span class="kpi-sub">0 = clean, 1 = highly biased</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Highest Lens Score</span>
      {% if report.scored_result.framework_scores %}
        {% set top = report.scored_result.framework_scores | sort(attribute='overall_score',reverse=true) | first %}
        <span class="kpi-value">{{ "%.3f"|format(top.overall_score) }}</span>
        <span class="kpi-sub">{{ top.framework_name }}</span>
      {% else %}
        <span class="kpi-value">—</span>
        <span class="kpi-sub">no analysis yet</span>
      {% endif %}
    </div>
    <div class="kpi">
      <span class="kpi-label">Flagged Texts</span>
      <span class="kpi-value">{{ report.scored_result.candidates | length }}</span>
      <span class="kpi-sub">score &gt; 0.5 in ≥1 lens</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Synergy Events</span>
      <span class="kpi-value" style="color:var(--secondary)">
        {{ report.scored_result.synergy_amplifications | length }}
      </span>
      <span class="kpi-sub">lens-pair convergences</span>
    </div>
  </div>

  {% if report.compliance_mapping %}
  <div class="risk-banner risk-{{ report.compliance_mapping.overall_compliance_risk }}">
    ⚠ Compliance Risk: {{ report.compliance_mapping.overall_compliance_risk | upper }}
    — {{ report.compliance_mapping.obligations | length }} obligation(s) triggered
  </div>
  {% endif %}

  <!-- ── Section: Summary ──────────────────────────────────────── -->
  <section id="summary" class="card">
    <h2>Summary</h2>
    <p style="line-height:1.7">{{ report.summary() }}</p>
    {% if report.scored_result.synergy_amplifications %}
    <div style="margin-top:1rem">
      <span style="font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em">
        Synergy Amplifications
      </span><br>
      {% for msg in report.scored_result.synergy_amplifications %}
        <span class="synergy-pill">{{ msg }}</span>
      {% endfor %}
    </div>
    {% endif %}
  </section>

  <!-- ── Section: Lens Scores (radar + bar + donut) ─────────────── -->
  <section id="lens-scores" class="card">
    <h2>Lens Scores</h2>
    <div class="charts-row-3">
      <div>
        <p style="font-size:.75rem;color:var(--muted);text-align:center;margin-bottom:.5rem">
          Cross-Cultural Radar
        </p>
        <div class="chart-wrap"><canvas id="radarChart"></canvas></div>
      </div>
      <div>
        <p style="font-size:.75rem;color:var(--muted);text-align:center;margin-bottom:.5rem">
          Score with 95% CI
        </p>
        <div class="chart-wrap"><canvas id="ciBarChart"></canvas></div>
      </div>
      <div>
        <p style="font-size:.75rem;color:var(--muted);text-align:center;margin-bottom:.5rem">
          Consensus Distribution
        </p>
        <div class="chart-wrap"><canvas id="doughnutChart"></canvas></div>
      </div>
    </div>

    <table class="data-table" style="margin-top:1.5rem">
      <thead>
        <tr>
          <th>Framework</th>
          <th>Raw Score</th>
          <th>Calibrated</th>
          <th>95% CI</th>
          <th>Confidence</th>
          <th>Flagged</th>
        </tr>
      </thead>
      <tbody>
        {% for fs in report.scored_result.framework_scores %}
        <tr>
          <td style="font-weight:600">{{ fs.framework_name }}</td>
          <td>
            <span class="badge {% if fs.overall_score > 0.6 %}badge-red{% elif fs.overall_score > 0.35 %}badge-amber{% else %}badge-green{% endif %}">
              {{ "%.3f"|format(fs.overall_score) }}
            </span>
          </td>
          <td>
            {% if fs.calibrated_score is not none %}
              {{ "%.3f"|format(fs.calibrated_score) }}
            {% else %}
              <span class="ci-text">not fitted</span>
            {% endif %}
          </td>
          <td class="ci-text">
            [{{ "%.3f"|format(fs.confidence_interval_95[0]) }},
             {{ "%.3f"|format(fs.confidence_interval_95[1]) }}]
          </td>
          <td>{{ "%.0f"|format(fs.confidence * 100) }}%</td>
          <td>{{ fs.flagged_candidates | length }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <!-- ── Section: Per-Text Heatmap ─────────────────────────────── -->
  <section id="heatmap" class="card">
    <h2>Per-Text Bias Heatmap</h2>
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem">
      Each row is one input text; columns are the four ethical lenses.
      Colour: green (low bias) → amber → red (high bias).
    </p>
    <div style="overflow-x:auto">
      <table class="heatmap-table">
        <thead>
          <tr>
            <th style="text-align:left">Text (truncated)</th>
            {% for fs in report.scored_result.framework_scores %}
            <th>{{ fs.framework_name.split()[0] }}</th>
            {% endfor %}
            <th>Max</th>
          </tr>
        </thead>
        <tbody id="heatmapBody">
          <!-- Populated by JS from per_text_scores data -->
        </tbody>
      </table>
    </div>
  </section>

  <!-- ── Section: WEAT Forest Plot ─────────────────────────────── -->
  <section id="weat" class="card">
    <h2>WEAT Analysis — Effect Sizes (d)</h2>
    {% if report.scored_result.weat_results %}
      <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem">
        Each point is a WEAT test. Effect size d &gt; 0 means target_a associates
        more with attribute_x. Red = p &lt; .05 (statistically significant).
        Error bars = 95% bootstrap CI.
      </p>
      <div id="forestPlot">
        {% for lens_id, suite in report.scored_result.weat_results.items() %}
          <p style="font-size:.8rem;font-weight:700;color:var(--secondary);margin:.75rem 0 .25rem">
            {{ lens_id.replace('_',' ') | title }}
          </p>
          {% for r in suite.results %}
          <div class="forest-row" data-d="{{ r.effect_size }}"
               data-ci-lo="{{ r.confidence_interval_95[0] }}"
               data-ci-hi="{{ r.confidence_interval_95[1] }}"
               data-p="{{ r.p_value }}">
            <div class="forest-label">
              {{ r.test_name.replace('_',' ') }}
              {% if r.p_value < 0.05 %}
                <span class="badge badge-red">p={{ "%.3f"|format(r.p_value) }}</span>
              {% else %}
                <span class="badge" style="background:rgba(255,255,255,.07);color:var(--muted)">
                  p={{ "%.3f"|format(r.p_value) }}
                </span>
              {% endif %}
            </div>
            <div class="forest-bar-wrap" id="fb_{{ loop.index }}_{{ loop.index0 }}">
              <!-- Rendered by JS -->
            </div>
            <div class="forest-val">d={{ "%.2f"|format(r.effect_size) }}</div>
          </div>
          {% endfor %}
        {% endfor %}
      </div>
    {% else %}
      <p style="color:var(--muted)">
        WEAT analysis was not run. Pass <code>run_weat=True</code> to
        <code>analyzer.analyze()</code> to enable it.
      </p>
    {% endif %}
  </section>

  <!-- ── Section: Dimension Breakdown ─────────────────────────── -->
  <section id="dimensions" class="card">
    <h2>Dimension Breakdown</h2>
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem">
      Stacked bars show which bias category drives each framework's score.
    </p>
    <div class="chart-wrap" style="height:320px"><canvas id="stackedDimChart"></canvas></div>
  </section>

  <!-- ── Section: Regulatory ───────────────────────────────────── -->
  <section id="regulatory" class="card">
    <h2>Regulatory Compliance Mapping</h2>
    {% if report.compliance_mapping and report.compliance_mapping.obligations %}
      <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem">
        {{ report.compliance_mapping.disclaimer }}
      </p>
      <table class="data-table">
        <thead>
          <tr>
            <th>Regulation</th><th>Article</th><th>Severity</th>
            <th>Obligation</th><th>Recommended Action</th>
          </tr>
        </thead>
        <tbody>
          {% for ob in report.compliance_mapping.obligations %}
          <tr>
            <td style="font-weight:600">{{ ob.regulation }}</td>
            <td>{{ ob.article }}</td>
            <td>
              <span class="badge
                {% if ob.severity=='critical' %}badge-red
                {% elif ob.severity=='high' %}badge-amber
                {% else %}badge-blue{% endif %}">
                {{ ob.severity }}
              </span>
            </td>
            <td style="font-size:.8rem">{{ ob.obligation_text }}</td>
            <td style="font-size:.8rem;color:var(--muted)">{{ ob.recommended_action }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p style="color:var(--muted)">No compliance mapping available.</p>
    {% endif %}
  </section>

  <!-- ── Section: Flagged Texts ─────────────────────────────────── -->
  <section id="candidates" class="card">
    <h2>Top Flagged Texts (score &gt; 0.5)</h2>
    {% set top_candidates = report.scored_result.candidates | sort(attribute='score',reverse=true) %}
    {% if top_candidates %}
      <table class="data-table">
        <thead>
          <tr><th>Text</th><th>Lens</th><th>Score</th><th>Dimensions</th></tr>
        </thead>
        <tbody>
          {% for c in top_candidates[:20] %}
          <tr>
            <td style="max-width:400px;white-space:normal;font-size:.8rem">{{ c.text[:200] }}{% if c.text|length > 200 %}…{% endif %}</td>
            <td><span class="badge badge-blue">{{ c.lens_id }}</span></td>
            <td>
              <span class="badge {% if c.score > 0.7 %}badge-red{% else %}badge-amber{% endif %}">
                {{ "%.3f"|format(c.score) }}
              </span>
            </td>
            <td style="font-size:.75rem;color:var(--muted)">
              {% if c.metadata and c.metadata.dimension_scores %}
                {% for dim, val in c.metadata.dimension_scores.items() if val > 0.3 %}
                  {{ dim.replace('_',' ') }}: {{ "%.2f"|format(val) }}
                {% endfor %}
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p style="color:var(--muted)">No texts exceeded the 0.5 bias threshold.</p>
    {% endif %}
  </section>

  <!-- ── Section: Provenance ───────────────────────────────────── -->
  <section id="provenance" class="card">
    <h2>Reproducibility & Provenance</h2>
    <details>
      <summary>View analysis metadata</summary>
      <table class="data-table" style="margin-top:1rem">
        <tr><td style="color:var(--muted)">Analysis ID</td><td>{{ report.scored_result.reproducibility.analysis_id }}</td></tr>
        <tr><td style="color:var(--muted)">Library Version</td><td>{{ report.scored_result.reproducibility.library_version }}</td></tr>
        <tr><td style="color:var(--muted)">Embedding Model</td><td>{{ report.scored_result.reproducibility.embedding_model_id }}</td></tr>
        <tr><td style="color:var(--muted)">Frameworks</td><td>{{ report.scored_result.reproducibility.framework_ids | join(', ') }}</td></tr>
        <tr><td style="color:var(--muted)">Random Seed</td><td>{{ report.scored_result.reproducibility.random_seed }}</td></tr>
        <tr><td style="color:var(--muted)">Bootstrap N</td><td>{{ report.scored_result.reproducibility.n_bootstrap_samples }}</td></tr>
        <tr><td style="color:var(--muted)">Python</td><td>{{ report.scored_result.reproducibility.python_version }}</td></tr>
        <tr><td style="color:var(--muted)">Recorded At</td><td>{{ report.scored_result.reproducibility.recorded_at }}</td></tr>
      </table>
      {% if report.scored_result.reproducibility.prototype_yaml_hashes %}
      <p style="font-size:.8rem;color:var(--muted);margin-top:1rem">Prototype YAML hashes:</p>
      <table class="data-table">
        {% for k, v in report.scored_result.reproducibility.prototype_yaml_hashes.items() %}
        <tr><td style="color:var(--muted)">{{ k }}</td><td style="font-family:monospace">{{ v }}</td></tr>
        {% endfor %}
      </table>
      {% endif %}
    </details>
  </section>

</main>

<!-- ──────────────────────────────────────────────────────────────── -->
<!-- JavaScript                                                       -->
<!-- ──────────────────────────────────────────────────────────────── -->
<script>
// ── Data injected from Python ────────────────────────────────────────
const lensLabels  = {{ lens_labels_json }};
const lensScores  = {{ lens_scores_json }};
const lensCI_lo   = {{ lens_ci_lo_json }};
const lensCI_hi   = {{ lens_ci_hi_json }};
const consensus   = {{ consensus_json }};
const dimData     = {{ dim_data_json }};     // {label: str, dims: {dim: score}}[]
const perTextData = {{ per_text_json }};     // {texts: str[], scores: {fid: float[]}}
const lensColors  = ['#6366f1','#22d3ee','#a855f7','#f59e0b'];

Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";
const gridColor = 'rgba(255,255,255,0.06)';

// ── 1. Radar chart ───────────────────────────────────────────────────
new Chart(document.getElementById('radarChart'), {
  type: 'radar',
  data: {
    labels: lensLabels,
    datasets: [{
      data: lensScores,
      backgroundColor: 'rgba(99,102,241,0.15)',
      borderColor: 'rgba(99,102,241,0.9)',
      borderWidth: 2,
      pointBackgroundColor: lensColors,
      pointRadius: 4,
    }]
  },
  options: {
    scales: { r: { beginAtZero:true, max:1,
      ticks:{display:false}, grid:{color:gridColor},
      pointLabels:{font:{size:11}} }},
    plugins:{legend:{display:false}}
  }
});

// ── 2. Score + CI bar chart ──────────────────────────────────────────
new Chart(document.getElementById('ciBarChart'), {
  type: 'bar',
  data: {
    labels: lensLabels,
    datasets: [
      {
        label: 'Score',
        data: lensScores,
        backgroundColor: lensColors.map(c => c + '99'),
        borderColor: lensColors,
        borderWidth: 2, borderRadius: 4,
      },
      {
        type: 'bar',
        label: '95% CI',
        data: lensScores.map((s,i) => [lensCI_lo[i], lensCI_hi[i]]),
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: lensColors.map(c => c),
        borderWidth: 2,
        barPercentage: 0.08,
      }
    ]
  },
  options: {
    scales: {
      y: { beginAtZero:true, max:1, grid:{color:gridColor} },
      x: { grid:{display:false} }
    },
    plugins:{legend:{display:false}}
  }
});

// ── 3. Doughnut ──────────────────────────────────────────────────────
new Chart(document.getElementById('doughnutChart'), {
  type: 'doughnut',
  data: {
    labels: ['Bias', 'Clean'],
    datasets: [{
      data: [consensus, Math.max(0, 1 - consensus)],
      backgroundColor: ['rgba(239,68,68,.7)','rgba(16,185,129,.25)'],
      borderWidth: 0,
      circumference: 180, rotation: 270
    }]
  },
  options: {
    cutout: '78%',
    plugins: {
      legend:{display:false},
      tooltip:{callbacks:{label: ctx => ctx.label + ': ' + ctx.parsed.toFixed(3)}}
    }
  }
});

// ── 4. Stacked dimension chart ───────────────────────────────────────
(function() {
  if (!dimData.length) return;
  const allDims = [...new Set(dimData.flatMap(d => Object.keys(d.dims)))];
  const dimColors = [
    '#6366f1','#22d3ee','#a855f7','#f59e0b','#ef4444','#10b981','#ec4899','#14b8a6'
  ];
  const datasets = allDims.map((dim, i) => ({
    label: dim.replace(/_/g,' '),
    data: dimData.map(d => d.dims[dim] || 0),
    backgroundColor: dimColors[i % dimColors.length] + 'bb',
    borderColor: dimColors[i % dimColors.length],
    borderWidth: 1,
  }));
  new Chart(document.getElementById('stackedDimChart'), {
    type: 'bar',
    data: { labels: dimData.map(d => d.label), datasets },
    options: {
      indexAxis: 'y',
      scales: {
        x: { stacked:true, beginAtZero:true, max:1, grid:{color:gridColor} },
        y: { stacked:true, grid:{display:false} }
      },
      plugins:{ legend:{ position:'bottom', labels:{font:{size:10}, boxWidth:12} } }
    }
  });
})();

// ── 5. Per-text heatmap (render cells) ──────────────────────────────
(function() {
  const tbody = document.getElementById('heatmapBody');
  if (!tbody || !perTextData.texts) return;
  const fids  = Object.keys(perTextData.scores);
  perTextData.texts.forEach((txt, i) => {
    const tr = document.createElement('tr');
    const tdTxt = document.createElement('td');
    tdTxt.className = 'text-col';
    tdTxt.textContent = txt.slice(0, 80) + (txt.length > 80 ? '…' : '');
    tr.appendChild(tdTxt);
    let maxScore = 0;
    fids.forEach(fid => {
      const s = (perTextData.scores[fid] || [])[i] || 0;
      if (s > maxScore) maxScore = s;
      const td = document.createElement('td');
      td.style.background = scoreToColor(s);
      td.style.color = s > 0.4 ? '#fff' : '#94a3b8';
      td.style.borderRadius = '4px';
      td.textContent = s.toFixed(2);
      tr.appendChild(td);
    });
    const tdMax = document.createElement('td');
    tdMax.style.fontWeight = '700';
    tdMax.style.color = maxScore > 0.6 ? '#fca5a5' : maxScore > 0.35 ? '#fcd34d' : '#6ee7b7';
    tdMax.textContent = maxScore.toFixed(2);
    tr.appendChild(tdMax);
    tbody.appendChild(tr);
  });
})();

function scoreToColor(s) {
  if (s <= 0) return 'rgba(16,185,129,0.08)';
  if (s < 0.2) return `rgba(16,185,129,${0.1 + s})`;
  if (s < 0.5) return `rgba(245,158,11,${0.15 + s * 0.6})`;
  return `rgba(239,68,68,${0.2 + s * 0.7})`;
}

// ── 6. Forest plot (WEAT) ────────────────────────────────────────────
(function() {
  const rows = document.querySelectorAll('.forest-row');
  if (!rows.length) return;
  // Find global range for axis scaling
  let minD = 0, maxD = 0;
  rows.forEach(row => {
    const lo = parseFloat(row.dataset.ciLo || row.dataset.d);
    const hi = parseFloat(row.dataset.ciHi || row.dataset.d);
    if (lo < minD) minD = lo;
    if (hi > maxD) maxD = hi;
  });
  const rangeD = Math.max(Math.abs(minD), Math.abs(maxD), 0.5) * 1.2;
  const toPercent = v => 50 + (v / rangeD) * 50;

  rows.forEach((row, rowIdx) => {
    const d  = parseFloat(row.dataset.d);
    const lo = parseFloat(row.dataset.ciLo || d - 0.1);
    const hi = parseFloat(row.dataset.ciHi || d + 0.1);
    const p  = parseFloat(row.dataset.p);
    const sig = p < 0.05;

    const wrap = row.querySelector('.forest-bar-wrap');
    if (!wrap) return;
    wrap.style.position = 'relative';

    // Null line
    const nullLine = document.createElement('div');
    nullLine.style.cssText = `position:absolute;left:50%;top:0;bottom:0;
      width:1px;background:rgba(255,255,255,0.2)`;
    wrap.appendChild(nullLine);

    // CI bar
    const ciBar = document.createElement('div');
    const loP = toPercent(lo), hiP = toPercent(hi);
    ciBar.style.cssText = `position:absolute;top:8px;height:4px;border-radius:2px;
      background:${sig ? 'rgba(99,102,241,0.5)' : 'rgba(148,163,184,0.3)'};
      left:${loP}%;width:${hiP - loP}%`;
    wrap.appendChild(ciBar);

    // Point
    const pt = document.createElement('div');
    const ptP = toPercent(d);
    pt.style.cssText = `position:absolute;top:5px;width:10px;height:10px;
      border-radius:50%;transform:translateX(-50%);
      background:${sig ? '#ef4444' : '#94a3b8'};
      left:${ptP}%`;
    wrap.appendChild(pt);
  });
})();

// ── Upload wiring — native form submission (most browser-compatible) ──
(function() {
  function submitForm(formId, file) {
    const form = document.getElementById(formId);
    // Swap in the chosen file via a new DataTransfer
    const dt = new DataTransfer();
    dt.items.add(file);
    form.querySelector('input[type=file]').files = dt.files;
    form.submit();
  }

  // Text file input change
  document.getElementById('textFile').addEventListener('change', function() {
    if (this.files[0]) document.getElementById('textForm').submit();
  });

  // Image file input change
  document.getElementById('imageFile').addEventListener('change', function() {
    if (this.files[0]) document.getElementById('imageForm').submit();
  });

  // Drag-and-drop onto the text drop zone
  var dz = document.getElementById('textDropZone');
  if (dz) {
    dz.addEventListener('dragover', function(e) {
      e.preventDefault(); dz.classList.add('drag-over');
    });
    dz.addEventListener('dragleave', function() { dz.classList.remove('drag-over'); });
    dz.addEventListener('drop', function(e) {
      e.preventDefault(); dz.classList.remove('drag-over');
      var file = e.dataTransfer.files[0];
      if (!file) return;
      var ext = file.name.split('.').pop().toLowerCase();
      var isImage = ['jpg','jpeg','png','gif','webp','bmp','tiff'].includes(ext);
      submitForm(isImage ? 'imageForm' : 'textForm', file);
    });
  }
})();

async function stopPlatform() {
  if (!confirm('Stop the EthiViz platform?')) return;
  try { await fetch('/stop', { method: 'POST' }); } catch {}
  document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;color:#94a3b8;font-family:sans-serif;text-align:center"><div><h1>Platform Stopped</h1><p>The server has been shut down.</p></div></div>';
}
</script>

</body>
</html>
"""


def generate_html_report(report: BiasReport) -> str:
    import jinja2

    sr = report.scored_result

    # Build template variables
    lens_labels = [fs.framework_name for fs in sr.framework_scores]
    lens_scores = [fs.overall_score for fs in sr.framework_scores]
    lens_ci_lo  = [fs.confidence_interval_95[0] for fs in sr.framework_scores]
    lens_ci_hi  = [fs.confidence_interval_95[1] for fs in sr.framework_scores]

    # Dimension data: one entry per framework
    dim_data = [
        {"label": fs.framework_name.split()[0], "dims": fs.dimension_scores}
        for fs in sr.framework_scores
    ]

    # Per-text scores — populated from metadata when available
    per_text_meta = sr.metadata.get("per_text_scores", {})
    texts_meta     = sr.metadata.get("texts", [])
    per_text_json_data = {
        "texts": texts_meta,
        "scores": per_text_meta,
    }

    template = jinja2.Template(HTML_TEMPLATE)
    return template.render(
        report=report,
        lens_labels_json=_safe_json(lens_labels),
        lens_scores_json=_safe_json(lens_scores),
        lens_ci_lo_json=_safe_json(lens_ci_lo),
        lens_ci_hi_json=_safe_json(lens_ci_hi),
        consensus_json=_safe_json(sr.consensus_score or 0.0),
        dim_data_json=_safe_json(dim_data),
        per_text_json=_safe_json(per_text_json_data),
    )
