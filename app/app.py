from __future__ import annotations
import sys, time, json, io
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.integration.pipeline import analyze_text, analyze_document, demo_mode_label
from src.integration.evaluation import evaluate_predictions, make_demo_predictions

st.set_page_config(page_title="Clarity Lint | Imperial Jade", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

JADE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap');
:root { --jade:#0e2a24; --jade2:#173c32; --jade3:#245244; --gold:#c5a45d; --gold2:#e1ca8a; --parch:#e9dfc8; --muted:#a9b9ae; }
.stApp { background: radial-gradient(ellipse at 80% -10%, #24483a 0%, #0c211d 45%, #081714 100%); color:var(--parch); font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:rgba(8,23,20,.85); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#102b24,#091a16); border-right:1px solid rgba(197,164,93,.38); }
[data-testid="stSidebar"] * { color:var(--parch); }
h1,h2,h3 { font-family:'Playfair Display',serif !important; color:#f1e7ce !important; letter-spacing:.2px; }
p, label, li { color:#d7d3c4; }
.hero { border:1px solid rgba(197,164,93,.48); border-radius:18px; padding:28px 32px; background:linear-gradient(115deg,rgba(24,61,50,.96),rgba(10,29,25,.92)); box-shadow:0 18px 50px rgba(0,0,0,.22); position:relative; overflow:hidden; }
.hero:after { content:"◈  ◇  ◈"; position:absolute; right:28px; top:24px; color:rgba(197,164,93,.22); font-size:32px; letter-spacing:12px; }
.eyebrow { color:var(--gold2); text-transform:uppercase; font:500 11px 'DM Mono',monospace; letter-spacing:3px; }
.hero h1 { font-size:42px; margin:9px 0 7px; line-height:1.12; }
.hero p { max-width:800px; font-size:14px; line-height:1.8; color:#c7d2c8; }
.gold-line { height:1px; background:linear-gradient(90deg,transparent,var(--gold),transparent); margin:18px 0; }
.panel { border:1px solid rgba(197,164,93,.28); background:rgba(18,47,39,.68); border-radius:14px; padding:18px 20px; margin-bottom:12px; }
.panel-title { color:var(--gold2); font:500 11px 'DM Mono',monospace; letter-spacing:2px; text-transform:uppercase; margin-bottom:9px; }
.metric { border:1px solid rgba(197,164,93,.32); background:linear-gradient(140deg,rgba(30,70,57,.85),rgba(10,31,26,.9)); padding:18px 18px 15px; border-radius:13px; min-height:110px; }
.metric .label { color:#afc0b5; font:500 10px 'DM Mono',monospace; letter-spacing:1.5px; text-transform:uppercase; }
.metric .value { color:#f0dfb5; font:600 29px 'Playfair Display',serif; margin-top:8px; }
.metric .sub { color:#8fa99a; font-size:11px; margin-top:4px; }
.pill { display:inline-block; border:1px solid rgba(197,164,93,.45); border-radius:99px; padding:4px 9px; color:#e1ca8a; font:10px 'DM Mono',monospace; letter-spacing:.8px; }
.small-muted { color:#9eb0a4; font-size:12px; }
blockquote { border-left:3px solid var(--gold); padding:10px 15px; background:rgba(197,164,93,.07); color:#e7dfca; }
.stButton>button, .stDownloadButton>button { border:1px solid #b89a58; background:linear-gradient(145deg,#c4a45f,#94763a); color:#10251f; font-weight:800; border-radius:8px; padding:9px 18px; }
.stButton>button:hover, .stDownloadButton>button:hover { border-color:#f0dca2; background:#e1ca8a; color:#081714; }
div[data-baseweb="tab-list"] { gap:7px; border-bottom:1px solid rgba(197,164,93,.25); }
button[data-baseweb="tab"] { color:#b5c5b8; }
button[data-baseweb="tab"][aria-selected="true"] { color:#f0dca2; border-bottom-color:#c5a45d; }
.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] { background:#0b201b; color:#eee4cc; border-color:#496c5a; }
[data-testid="stDataFrame"] { border:1px solid rgba(197,164,93,.25); border-radius:10px; overflow:hidden; }
hr { border-color:rgba(197,164,93,.22); }
footer { visibility:hidden; }
</style>
"""
st.markdown(JADE_CSS, unsafe_allow_html=True)

LABELS = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]
LABEL_COLORS = {"no_ambiguity":"#8da99a","vague":"#c5a45d","attachment":"#df9b64","scope":"#bd8278","pronoun":"#8aa7c4"}

def metric_card(label, value, sub):
    st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def hero(kicker, title, desc):
    st.markdown(f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{desc}</p><div class="gold-line"></div><span class="pill">HUMAN-IN-THE-LOOP NLP</span>&nbsp;&nbsp;<span class="pill">IMPERIAL JADE EDITION</span></div>', unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.markdown("<div style='font-family:Playfair Display;font-size:28px;color:#e1ca8a;padding:8px 0 0'>◈ CLARITY LINT</div><div style='font:10px DM Mono;color:#9eb0a4;letter-spacing:2px'>IMPERIAL JADE / PERSON 05</div>", unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("WORKSPACE", ["Overview", "Analyze Text", "Document Review", "Evaluation Lab", "Error Analysis", "Integration Status", "Viva & Demo"], label_visibility="visible")
        st.markdown("---")
        st.markdown("<div class='panel-title'>SYSTEM STATUS</div>", unsafe_allow_html=True)
        st.markdown("<span class='pill'>DEMO-SAFE MODE</span>", unsafe_allow_html=True)
        st.caption("Demo outputs are illustrative. Replace adapters with the team's measured modules before reporting results.")
        st.markdown("<div class='gold-line'></div><div class='small-muted'>Person 5 · Integration, dashboard & evaluation</div>", unsafe_allow_html=True)
        return page

page = sidebar()

def render_overview():
    hero("Clarity intelligence / 01", "Make meaning unmistakable.", "A focused NLP workbench for requirements, contracts, and policy text. Surface possible ambiguity, compare independent detection methods, and help writers make intent explicit.")
    st.write("")
    cols = st.columns(4)
    metric_card("Ambiguity families", "04", "Vague · Attachment · Scope · Reference")
    metric_card("Detection paths", "03", "Rules · DistilBERT · Prompt baseline")
    metric_card("Review principle", "Human", "Suggestions, never legal verdicts")
    metric_card("Evaluation", "Honest", "Held-out labels required for real metrics")
    st.write("")
    left, right = st.columns([1.25, .75], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">THE PIPELINE</div><h3>From sentence to clarity</h3>', unsafe_allow_html=True)
        steps = [
            ("01", "Input", "Paste a clause or review a text file."),
            ("02", "Detect", "Run rules and, when installed, the trained classifier."),
            ("03", "Explain", "Show evidence spans and plausible competing readings."),
            ("04", "Refine", "Offer intent-aware rewrites for human approval."),
            ("05", "Evaluate", "Compare methods on the same frozen test set.")
        ]
        for n, title, desc in steps:
            st.markdown(f"<div style='display:flex;gap:13px;margin:15px 0'><div style='color:#c5a45d;font:14px DM Mono;min-width:30px'>{n}</div><div><b style='color:#f0e4c7'>{title}</b><div class='small-muted'>{desc}</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">DESIGN ETHOS</div><h3>Precision over certainty</h3><p>Long or complex text is not automatically ambiguous. Each flag should point to a plausible alternate interpretation.</p><div class="gold-line"></div><p class="small-muted">Project-defined ambiguity rate = flagged sentences ÷ total sentences × 100. It is not a validated legal-risk score.</p></div>', unsafe_allow_html=True)
        st.info("Start with **Analyze Text** for a guided demonstration, or use **Evaluation Lab** to load the team's test predictions.")

def render_analysis():
    hero("Sentence workbench / 02", "Analyze a clause.", "Inspect a sentence, compare detector signals, and review possible meanings. The bundled demo detector is deliberately labeled as illustrative until team modules are connected.")
    demo_examples = {
        "Attachment ambiguity": "The admin monitors the user with the sensor.",
        "Vague term": "The supplier shall respond soon.",
        "Pronoun/reference": "When the analyst met the manager, they approved the report.",
        "Scope ambiguity": "The system does not notify all users and administrators.",
        "Clear sentence": "The service must return HTTP 200 within 500 milliseconds."
    }
    chosen = st.selectbox("Load an example", ["Write my own"] + list(demo_examples.keys()))
    default_text = "" if chosen == "Write my own" else demo_examples[chosen]
    text_value = st.text_area("Sentence or short clause", value=default_text, height=120, placeholder="Paste requirements, contract clauses, or policy language…")
    c1, c2 = st.columns([1, 3])
    with c1:
        run = st.button("Analyze sentence", type="primary", use_container_width=True)
    with c2:
        st.caption("Preserves punctuation, negation, modifiers, and pronouns. No text is sent to an external API by this demo app.")
    if run:
        if not text_value.strip():
            st.warning("Enter a sentence before running analysis.")
        else:
            with st.spinner("Inspecting linguistic signals…"):
                result = analyze_text(text_value.strip())
            st.session_state["last_analysis"] = result
    result = st.session_state.get("last_analysis")
    if result:
        st.markdown("---")
        left, right = st.columns([1.05, .95], gap="large")
        with left:
            st.markdown('<div class="panel-title">DETECTION RESULT</div>', unsafe_allow_html=True)
            if result["detections"]:
                for det in result["detections"]:
                    st.markdown(f"<div class='panel'><span class='pill'>{det['label'].upper()}</span><p style='margin-top:12px'><b>Evidence</b>: <code>{det.get('span') or 'Not provided'}</code></p><p>{det.get('reason','Possible ambiguity detected.')}</p><div class='small-muted'>Source: {det.get('source','unknown')} · Confidence: {det.get('confidence') if det.get('confidence') is not None else 'not provided'}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='panel'><span class='pill'>NO FLAG RETURNED</span><p>No configured detector flagged this sentence. This does not prove that the sentence is unambiguous.</p></div>", unsafe_allow_html=True)
        with right:
            st.markdown('<div class="panel-title">EXPLANATION & REWRITE</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='panel'><b>Why review it?</b><p>{result.get('explanation','No explanation module connected yet.')}</p></div>", unsafe_allow_html=True)
            readings = result.get("readings", [])
            if readings:
                st.markdown("**Possible readings**")
                for i, r in enumerate(readings, 1):
                    st.markdown(f"{i}. {r}")
            rewrites = result.get("rewrites", [])
            if rewrites:
                st.markdown("**Candidate rewrites**")
                for i, rw in enumerate(rewrites, 1):
                    st.text_area(f"Option {i}", value=rw, height=65, key=f"rewrite_{i}_{hash(text_value)}")
                st.caption("Choose the rewrite matching the intended meaning. Do not accept a rewrite that adds obligations or details.")
            st.download_button("Export analysis JSON", data=json.dumps(result, indent=2), file_name="clarity_lint_analysis.json", mime="application/json")
        st.caption(f"Mode: {result.get('mode','unknown')} · elapsed: {result.get('latency_ms',0):.2f} ms (local wall-clock measurement for this call only)")

def render_document():
    hero("Document review / 03", "Read the whole document.", "Upload a plain-text file or paste content to get sentence-level review and a document summary. File support is intentionally conservative in this first version.")
    upload = st.file_uploader("Upload a UTF-8 .txt file", type=["txt"])
    pasted = st.text_area("Or paste document text", height=160, placeholder="Paste policy, requirement, or contract text here…")
    if st.button("Review document", type="primary"):
        raw = ""
        if upload:
            try: raw = upload.getvalue().decode("utf-8-sig")
            except UnicodeDecodeError: st.error("File is not valid UTF-8. Save it as UTF-8 text and retry.")
        else: raw = pasted
        if not raw.strip(): st.warning("Upload a text file or paste document content.")
        else:
            with st.spinner("Reviewing sentences…"):
                doc = analyze_document(raw)
            st.session_state["last_document"] = doc
    doc = st.session_state.get("last_document")
    if doc:
        st.markdown("---")
        total, flagged, rate, elapsed = st.columns(4)
        with total: metric_card("Sentences", str(doc["sentence_count"]), "Extracted by simple sentence splitter")
        with flagged: metric_card("Flagged", str(doc["flagged_count"]), "At least one detection")
        with rate: metric_card("Ambiguity rate", f"{doc['ambiguity_rate']:.1f}%", "Project-defined; not legal risk")
        with elapsed: metric_card("Analysis time", f"{doc['latency_ms']:.1f} ms", "Local wall-clock measurement")
        st.markdown("### Type breakdown")
        counts = doc["type_counts"]
        chart_df = pd.DataFrame({"Type": list(counts.keys()), "Count": list(counts.values())})
        if chart_df["Count"].sum() > 0:
            fig = px.bar(chart_df, x="Type", y="Count", color="Type", color_discrete_map=LABEL_COLORS, template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e9dfc8", showlegend=False, margin=dict(l=5,r=5,t=10,b=5))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No demo rules triggered on this document.")
        table_rows = []
        for item in doc["sentences"]:
            table_rows.append({"Sentence": item["text"], "Flagged": bool(item["detections"]), "Types": ", ".join(d["label"] for d in item["detections"]) or "—", "Explanation": item.get("explanation","")})
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        st.download_button("Download document report (CSV)", data=pd.DataFrame(table_rows).to_csv(index=False), file_name="clarity_lint_document_report.csv", mime="text/csv")

def render_evaluation():
    hero("Evaluation lab / 04", "Measure what matters.", "Use the same held-out test examples and label mapping for every method. Demo numbers are synthetic fixtures to validate charts—not project results.")
    st.warning("Demo mode is active until you load real gold labels and predictions. Do not copy illustrative metrics into your report.")
    uploaded = st.file_uploader("Load evaluation CSV (optional)", type=["csv"], key="eval_csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("Preview", df.head(8))
        required = {"gold_label"}
        if not required.issubset(df.columns):
            st.error("CSV needs a gold_label column. Add prediction columns named rules_pred, model_pred, prompt_pred to compare methods.")
        else:
            pred_cols = [c for c in ["rules_pred","model_pred","prompt_pred"] if c in df.columns]
            if pred_cols:
                metrics, reports = evaluate_predictions(df, pred_cols)
                for method, report in reports.items():
                    st.markdown(f"### {method}")
                    st.json(report)
            else: st.info("No recognized prediction columns found.")
    else:
        metrics = make_demo_predictions()
        c1,c2,c3 = st.columns(3)
        for col, method in zip([c1,c2,c3], ["rules_pred","model_pred","prompt_pred"]):
            report = metrics[method]
            with col:
                st.markdown(f"<div class='panel'><div class='panel-title'>{method.replace('_',' ').upper()}</div><h3>Illustrative only</h3><p class='small-muted'>Replace with measured test-set output.</p><div class='gold-line'></div><p>Macro-F1 fixture: {report['macro_f1']:.2f}</p></div>", unsafe_allow_html=True)
        st.markdown("### Example confusion matrix — fixture data")
        method = st.selectbox("Method", ["rules_pred","model_pred","prompt_pred"])
        cm = metrics[method]["confusion_matrix"]
        fig = px.imshow(cm, x=LABELS, y=LABELS, text_auto=True, aspect="auto", color_continuous_scale=["#102820","#c5a45d"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e9dfc8", xaxis_title="Predicted label", yaxis_title="Gold label")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Required final evaluation checklist")
    for item in ["Freeze and document test split IDs.", "Use identical test sentence IDs for rules, model, and prompt baseline.", "Report per-class precision, recall, F1 and macro-F1.", "Include confusion matrices and representative errors.", "Measure latency on a named machine/environment.", "Do not tune thresholds on the test set."]:
        st.checkbox(item, key="check_"+str(abs(hash(item))))

def render_errors():
    hero("Failure review / 05", "Inspect the misses.", "Error analysis is part of the deliverable, not an afterthought. Record the evidence, likely cause, and what should change without tuning against the final test set.")
    st.markdown('<div class="panel"><div class="panel-title">ERROR LOG TEMPLATE</div><p>Use this editable table as a starting point. Replace examples with observed failures from your frozen test set.</p></div>', unsafe_allow_html=True)
    default = pd.DataFrame([
        {"sentence_id":"EX-001","gold_label":"attachment","predicted_label":"no_ambiguity","method":"rules","error_type":"False negative","likely_cause":"PP attachment pattern not covered","next_action":"Review dev examples; add conservative rule if justified"},
        {"sentence_id":"EX-002","gold_label":"no_ambiguity","predicted_label":"vague","method":"rules","error_type":"False positive","likely_cause":"Trigger word treated as sufficient evidence","next_action":"Require context/evidence span; test clear negatives"},
        {"sentence_id":"EX-003","gold_label":"pronoun","predicted_label":"scope","method":"model","error_type":"Class confusion","likely_cause":"Small or imbalanced training data","next_action":"Inspect train/dev label counts and similar examples"}
    ])
    edited = st.data_editor(default, num_rows="dynamic", use_container_width=True, key="error_editor")
    st.download_button("Export error analysis CSV", data=edited.to_csv(index=False), file_name="error_analysis_template.csv", mime="text/csv")
    st.caption("Rows above are illustrative templates, not observed errors. Replace them with actual error examples before submission.")

def render_integration():
    hero("Integration console / 06", "One contract. Three methods.", "The UI calls adapters rather than embedding detection logic in Streamlit. Each module owner remains responsible for fixing their module-level bugs.")
    st.markdown("### Shared label contract")
    st.code("no_ambiguity | vague | attachment | scope | pronoun", language="text")
    st.markdown("### Canonical detection record")
    st.code(json.dumps({"sentence_id":"S001","text":"The admin monitors the user with the sensor.","gold_label":"attachment","predictions":[{"source":"rules","label":"attachment","span":"with the sensor","confidence":None,"reason":"The phrase may attach in more than one way."}],"readings":["The admin uses a sensor to monitor the user.","The user has a sensor associated with them."],"rewrites":["The admin uses the sensor to monitor the user."]}, indent=2), language="json")
    status = [
        ("Person 2 · Rules", "src/rules/detect.py", "Optional import adapter; demo fallback active"),
        ("Person 3 · DistilBERT", "src/model/predict.py", "Optional import adapter; model checkpoint not bundled"),
        ("Person 4 · Explanations", "src/explanations/explain.py", "Optional import adapter; safe demo templates active"),
        ("Person 4 · Prompt baseline", "src/explanations/baseline.py", "Optional import adapter; not called without configuration")
    ]
    for owner, path, note in status:
        st.markdown(f"<div class='panel'><b>{owner}</b><div class='small-muted'>{path}</div><p>{note}</p></div>", unsafe_allow_html=True)
    st.info("Place teammates' modules at the paths above or update the adapter configuration in `src/integration/pipeline.py`. Missing modules should be visible—not silently presented as trained models.")

def render_viva():
    hero("Presentation suite / 07", "Explain the engineering.", "A concise demo flow and viva notes for Person 5. The goal is to explain integration decisions, evaluation integrity, and limitations clearly.")
    st.markdown("### Suggested 4-minute demo")
    demo = [
        ("0:00–0:30", "Introduce the problem", "Clarity Lint flags possible ambiguity in requirements, contracts, and policies."),
        ("0:30–1:15", "Analyze one sentence", "Use “The admin monitors the user with the sensor.” Show the competing readings."),
        ("1:15–2:00", "Review a document", "Show sentence counts, type breakdown, and the project-defined ambiguity rate."),
        ("2:00–3:00", "Compare methods", "Explain rules vs DistilBERT vs prompt baseline on the same held-out test set."),
        ("3:00–4:00", "Discuss limitations", "Show one false positive and one false negative; explain why human review matters.")
    ]
    for t, title, desc in demo:
        st.markdown(f"<div class='panel'><span class='pill'>{t}</span><h3 style='margin-top:8px'>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)
    st.markdown("### Viva answer: your contribution")
    st.markdown("> I built the Streamlit integration layer for Clarity Lint. It connects rule-based detection, the DistilBERT classifier, and the explanation/rewrite module through a shared schema. I designed the dashboard to show sentence-level evidence and document summaries, and I prepared evaluation utilities to compare all methods on the same held-out test set using per-class precision, recall, F1, macro-F1, confusion matrices, and latency. I distinguish demo fixtures from measured results and present every flag as a suggestion for human review.")
    st.markdown("### Questions to prepare")
    with st.expander("Why not put all NLP logic in app.py?"):
        st.write("Separating UI, integration adapters, and model/rule logic makes each module independently testable and lets teammates own their code.")
    with st.expander("What is the ambiguity rate?"):
        st.write("A project-defined descriptive statistic: flagged sentences divided by total sentences, multiplied by 100. It is not a validated legal-risk score.")
    with st.expander("Why compare on the same test set?"):
        st.write("Otherwise differences could come from different examples rather than method quality. Test data should stay untouched until choices are finalized.")
    with st.expander("What if rules and model disagree?"):
        st.write("Show the disagreement. It is a useful review signal and an opportunity for error analysis, not a reason to silently choose one output.")

if page == "Overview": render_overview()
elif page == "Analyze Text": render_analysis()
elif page == "Document Review": render_document()
elif page == "Evaluation Lab": render_evaluation()
elif page == "Error Analysis": render_errors()
elif page == "Integration Status": render_integration()
elif page == "Viva & Demo": render_viva()

st.markdown("<div class='gold-line'></div><div style='text-align:center;color:#728f80;font:10px DM Mono;letter-spacing:2px;padding:10px'>CLARITY LINT · IMPERIAL JADE · PERSON 05 · REVIEW BEFORE RELYING</div>", unsafe_allow_html=True)
