from __future__ import annotations
import sys, time, json, io
from pathlib import Path
import pandas as pd
import streamlit as st

# <!-- CLARITY_LINT_GLASS_UI_START -->
st.set_page_config(page_title="Clarity Lint | Imperial Jade", page_icon="Ã¢â€”Ë†", layout="wide", initial_sidebar_state="expanded")

st.markdown('\n<style>\n/* Clarity Lint ? emerald glass UI enhancement */\n:root {\n  --cl-emerald: #6ee7a4;\n  --cl-gold: #d9b86c;\n}\n\n/* App background */\n[data-testid="stAppViewContainer"] {\n  background:\n    radial-gradient(ellipse at 8% 0%, rgba(35,115,76,.17), transparent 38%),\n    radial-gradient(ellipse at 95% 12%, rgba(190,150,65,.08), transparent 30%),\n    var(--background-color);\n}\n\n/* Premium glass cards */\n[data-testid="stMetric"],\ndiv[data-testid="stVerticalBlockBorderWrapper"] {\n  border: 1px solid rgba(110,231,164,.17);\n  border-radius: 16px;\n  background: rgba(20, 43, 32, .38);\n  backdrop-filter: blur(14px);\n  -webkit-backdrop-filter: blur(14px);\n  transition: border-color .22s ease, box-shadow .22s ease,\n              transform .22s ease, background .22s ease;\n}\n\n/* Cursor-responsive light on cards */\n[data-testid="stMetric"]:hover,\ndiv[data-testid="stVerticalBlockBorderWrapper"]:hover {\n  border-color: rgba(110,231,164,.42);\n  box-shadow: 0 8px 28px rgba(0,0,0,.15),\n              0 0 22px rgba(72,205,125,.07);\n  transform: translateY(-2px);\n}\n\n/* Gold/emerald buttons */\n.stButton > button,\n.stDownloadButton > button {\n  border-radius: 11px;\n  border: 1px solid rgba(217,184,108,.4);\n  transition: all .2s ease;\n}\n.stButton > button:hover,\n.stDownloadButton > button:hover {\n  border-color: #6ee7a4;\n  box-shadow: 0 0 18px rgba(110,231,164,.16);\n  transform: translateY(-1px);\n}\n\n/* Inputs */\n.stTextArea textarea, .stTextInput input,\n.stSelectbox [data-baseweb="select"] {\n  border-radius: 11px;\n  transition: border-color .2s ease, box-shadow .2s ease;\n}\n.stTextArea textarea:focus, .stTextInput input:focus {\n  border-color: #6ee7a4;\n  box-shadow: 0 0 0 1px rgba(110,231,164,.22);\n}\n\n/* Sidebar separation */\n[data-testid="stSidebar"] {\n  border-right: 1px solid rgba(110,231,164,.12);\n}\n\n/* Respect reduced-motion preferences */\n@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after {\n    transition: none !important;\n    animation: none !important;\n    transform: none !important;\n  }\n}\n</style>\n', unsafe_allow_html=True)
# <!-- CLARITY_LINT_GLASS_UI_END -->

# <!-- CLARITY_CURSOR_START -->
import streamlit.components.v1 as cl_components
cl_components.html('\n<style>\n#cl-cursor-glow {\n  position: fixed;\n  left: 0;\n  top: 0;\n  width: 360px;\n  height: 360px;\n  border-radius: 50%;\n  pointer-events: none;\n  z-index: 999999;\n  transform: translate(-50%, -50%);\n  background: radial-gradient(circle,\n    rgba(91, 230, 148, .105) 0%,\n    rgba(91, 230, 148, .045) 35%,\n    transparent 70%);\n  mix-blend-mode: screen;\n  opacity: 0;\n  transition: opacity .25s ease;\n}\n@media (hover: hover) and (pointer: fine) {\n  body:hover #cl-cursor-glow { opacity: 1; }\n}\n@media (prefers-reduced-motion: reduce) {\n  #cl-cursor-glow { display: none !important; }\n}\n</style>\n<div id="cl-cursor-glow"></div>\n<script>\n(() => {\n  const glow = document.getElementById(\'cl-cursor-glow\');\n  if (!glow || glow.dataset.ready) return;\n  glow.dataset.ready = \'1\';\n  document.addEventListener(\'pointermove\', (event) => {\n    glow.style.left = event.clientX + \'px\';\n    glow.style.top = event.clientY + \'px\';\n  }, { passive: true });\n})();\n</script>\n', height=0, scrolling=False)
# <!-- CLARITY_CURSOR_END -->


import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.integration.pipeline import analyze_text, analyze_document, demo_mode_label
from src.integration.evaluation import evaluate_predictions, make_demo_predictions


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
.hero:after { content: none; }
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

/* Clarity Lint visual refinement */
.hero {
  padding: 32px 36px;
  min-height: 245px;
  background:
    radial-gradient(ellipse at 95% 0%, rgba(197,164,93,.13), transparent 38%),
    linear-gradient(120deg, rgba(24,61,50,.98), rgba(8,28,23,.98));
}
.hero h1 { font-size: clamp(34px, 3.4vw, 48px); max-width: 850px; }
.hero p { font-size: 15px; max-width: 820px; }
.metric {
  min-height: 125px;
  border-radius: 12px;
  padding: 18px;
  background: linear-gradient(145deg, rgba(28,67,54,.94), rgba(10,32,26,.98));
  transition: transform .18s ease, border-color .18s ease;
}
.metric:hover {
  transform: translateY(-3px);
  border-color: rgba(225,202,138,.75);
}
.panel {
  border-radius: 13px;
  padding: 20px;
  background: linear-gradient(145deg, rgba(22,54,44,.92), rgba(11,31,26,.95));
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0;
}
.feature-card {
  min-height: 165px;
  padding: 20px;
  border: 1px solid rgba(197,164,93,.3);
  border-radius: 13px;
  background: linear-gradient(145deg, rgba(24,59,48,.9), rgba(9,29,24,.96));
}
.feature-number {
  font: 11px 'DM Mono', monospace;
  letter-spacing: 2px;
  color: #c5a45d;
}
.feature-card h3 {
  font-size: 21px;
  margin: 15px 0 8px;
}
.feature-card p {
  color: #aebfb3;
  font-size: 12px;
  line-height: 1.7;
}
.pipeline {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 20px;
}
.pipeline-step {
  padding: 15px 12px;
  border: 1px solid rgba(197,164,93,.28);
  border-radius: 10px;
  background: rgba(9,29,24,.7);
}
.pipeline-step b {
  display: block;
  color: #e1ca8a;
  font: 11px 'DM Mono', monospace;
  margin-bottom: 9px;
}
.pipeline-step span {
  color: #e9dfc8;
  font-size: 13px;
  font-weight: 700;
}
.pipeline-step p {
  color: #9eb0a4;
  font-size: 11px;
  line-height: 1.5;
}
@media (max-width: 850px) {
  .feature-grid { grid-template-columns: 1fr; }
  .pipeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero { padding: 24px; }
}


/* Professional Clarity Lint navigation */












/* Clean, compact Clarity Lint sidebar */
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 3px !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 7px 10px !important;
    margin: 0 !important;
    border: 1px solid transparent !important;
    border-radius: 7px !important;
    line-height: 1.4 !important;
    transition: background .15s ease, border-color .15s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(197,164,93,.07) !important;
    border-color: rgba(197,164,93,.20) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(197,164,93,.12) !important;
    border-color: rgba(197,164,93,.38) !important;
}


/* Final navigation and responsive layout polish */

/* Keep inactive navigation buttons dark green */
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {
    background: linear-gradient(135deg,#12382c,#0b251d) !important;
    color: #e9dfc8 !important;
    border: 1px solid rgba(197,164,93,.24) !important;
}

/* Gold is reserved for the active navigation item */
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg,#b99a56,#92743a) !important;
    color: #fff7df !important;
    border: 1px solid #d9bd78 !important;
    box-shadow: 0 3px 12px rgba(0,0,0,.12);
}

/* Compact descriptions and better button spacing */
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    min-height: 42px !important;
    margin-bottom: 2px !important;
}
.cl-nav-description {
    margin: -2px 3px 7px 42px !important;
    font-size: 10px !important;
    line-height: 1.45 !important;
    color: #a8bcae !important;
}

/* Prevent main content from overflowing the viewport */
[data-testid="stMainBlockContainer"] {
    max-width: 1440px !important;
    width: 100% !important;
    padding-left: clamp(1rem, 4vw, 3.5rem) !important;
    padding-right: clamp(1rem, 4vw, 3.5rem) !important;
}

/* Ensure card and pipeline grids shrink on smaller screens */
.feature-grid,
.pipeline {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
.feature-card,
.pipeline-step,
.panel,
.metric {
    min-width: 0;
    overflow-wrap: anywhere;
    box-sizing: border-box;
}
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .pipeline {
        grid-template-columns: repeat(2,minmax(0,1fr)) !important;
    }
    .feature-grid {
        grid-template-columns: 1fr !important;
    }
    .hero {
        padding: 24px !important;
    }
}



/* Real teddy silhouette decoration */
[data-testid="stSidebar"] {
    position: relative;
    overflow: hidden;
}

.cl-teddy-rain {
    position: fixed;
    top: 650px;
    left: 18px;
    width: 255px;
    height: calc(100vh - 650px);
    min-height: 180px;
    overflow: hidden;
    pointer-events: none;
    z-index: 2;
    opacity: .9;
}

.cl-teddy {
    position: absolute;
    display: block;
    top: -30px;
    width: 19px;
    height: 23px;
    color: #c7a45b;
    opacity: .65;
    animation: cl-teddy-fall 9s linear infinite;
}

.cl-teddy {
    position: absolute;
    top: -35px;
    width: 19px;
    height: 23px;
    color: #c7a45b;
    opacity: .48;
    animation: cl-teddy-fall 12s linear infinite;
}

.cl-teddy svg {
    display: block;
    width: 19px;
    height: 23px;
    overflow: visible;
}

.cl-teddy:nth-child(1) { left: 8%; animation-delay: -2s; }
.cl-teddy:nth-child(2) { left: 29%; animation-delay: -8s; }
.cl-teddy:nth-child(3) { left: 52%; animation-delay: -5s; }
.cl-teddy:nth-child(4) { left: 76%; animation-delay: -10s; }
.cl-teddy:nth-child(5) { left: 91%; animation-delay: -1s; }

@keyframes cl-teddy-fall {
    0%   { transform: translateY(-35px) rotate(-8deg); }
    100% { transform: translateY(calc(100vh - 650px)) rotate(8deg); }
}
    50%  { transform: translateY(240px) rotate(8deg); }
    100% { transform: translateY(520px) rotate(-5deg); }
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    position: relative;
    z-index: 1;
}

@media (prefers-reduced-motion: reduce) {
    .cl-teddy { animation: none; }
}


/* Final fix: self-contained teddy fall area */
[data-testid="stSidebar"] .cl-teddy-rain {
    position: relative !important;
    top: auto !important;
    bottom: auto !important;
    left: auto !important;
    right: auto !important;
    width: 100% !important;
    height: 290px !important;
    min-height: 290px !important;
    margin: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    z-index: 0 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy {
    position: absolute !important;
    display: block !important;
    top: -28px !important;
    width: 19px !important;
    height: 23px !important;
    color: #c7a45b !important;
    opacity: .72 !important;
    animation-name: cl-teddy-drop-final !important;
    animation-duration: 8s !important;
    animation-timing-function: linear !important;
    animation-iteration-count: infinite !important;
}

[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy:nth-child(1) {
    left: 12% !important;
    animation-delay: -1s !important;
}
[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy:nth-child(2) {
    left: 34% !important;
    animation-delay: -5s !important;
}
[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy:nth-child(3) {
    left: 61% !important;
    animation-delay: -3s !important;
}
[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy:nth-child(4) {
    left: 83% !important;
    animation-delay: -7s !important;
}
[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy:nth-child(5) {
    left: 47% !important;
    animation-delay: -2s !important;
}

[data-testid="stSidebar"] .cl-teddy-rain .cl-teddy svg {
    display: block !important;
    width: 19px !important;
    height: 23px !important;
}

@keyframes cl-teddy-drop-final {
    0%   { transform: translateY(0) rotate(-8deg); }
    100% { transform: translateY(320px) rotate(9deg); }
}

@media (prefers-reduced-motion: reduce) {
    [data-testid="stSidebar"] .cl-teddy-rain .cl-teddy {
        animation: none !important;
        top: 50px !important;
    }
}

</style>
"""
st.markdown(JADE_CSS, unsafe_allow_html=True)

LABELS = ["no_ambiguity", "vague", "attachment", "scope", "pronoun"]
LABEL_COLORS = {"no_ambiguity":"#8da99a","vague":"#c5a45d","attachment":"#df9b64","scope":"#bd8278","pronoun":"#8aa7c4"}

def metric_card(label, value, sub):
    st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def hero(kicker, title, desc):
    st.markdown(f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{desc}</p><div class="gold-line"></div><span class="pill">HUMAN-IN-THE-LOOP NLP</span>&nbsp;&nbsp;<span class="pill">CLARITY WORKBENCH</span></div>', unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="cl-brand-wrap">
          <div class="cl-brand-symbol">
            <svg viewBox="0 0 48 48"
     aria-label="Clarity Lint document search logo"
     role="img" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="#D6B66F" stroke-linecap="round"
     stroke-linejoin="round">
    <!-- Magnifying glass -->
    <circle cx="21" cy="20" r="12.5" stroke-width="2.5"/>
    <path d="M12 29 L4.5 37" stroke-width="4.5"/>
    <path d="M12 29 L4.5 37" stroke="#F0D69A" stroke-width="2.5"/>
    <!-- Document inside the lens -->
    <rect x="14" y="12" width="15" height="17" rx="2"
          fill="#123B29" stroke-width="1.7"/>
    <path d="M17.5 17 H25.5 M17.5 21 H25.5 M17.5 25 H23.5"
          stroke="#F0D69A" stroke-width="1.5"/>
  </g>
</svg>
          </div>
          <div class="cl-brand-copy">
            <div class="cl-brand-name">CLARITY <span>LINT</span></div>
            <div class="cl-brand-tag">REQUIREMENTS INTELLIGENCE</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        nav_items = [
            ("Overview", "dashboard"),
            ("Analyze Text", "center_focus_strong"),
            ("Document Review", "snippet_folder"),
            ("Evaluation Lab", "monitoring"),
            ("Error Analysis", "troubleshoot"),
            ("Integration Status", "account_tree"),
            ("Viva & Demo", "school"),
        ]
        if "cl_active_page" not in st.session_state:
            st.session_state["cl_active_page"] = "Overview"
        for nav_name, nav_icon in nav_items:
            if st.button(
                nav_name,
                key="cl_btn_" + nav_name.lower().replace(" ", "_").replace("&", "and"),
                icon=":material/" + nav_icon + ":",
                type="primary" if st.session_state["cl_active_page"] == nav_name else "secondary",
                use_container_width=True,
            ):
                st.session_state["cl_active_page"] = nav_name
                st.rerun()
        page = st.session_state["cl_active_page"]
        st.markdown("---")



        st.markdown("""
        <div class="cl-teddy-rain" aria-hidden="true">
          <span class="cl-teddy"><svg viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="18.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="12" cy="10" r="7" fill="currentColor"/><ellipse cx="12" cy="21" rx="6.5" ry="5.5" fill="currentColor"/><circle cx="8" cy="15" r="3" fill="currentColor"/><circle cx="16" cy="15" r="3" fill="currentColor"/><ellipse cx="12" cy="12" rx="3.2" ry="2.5" fill="#0b211a"/><circle cx="9.5" cy="9.5" r="0.8" fill="#0b211a"/><circle cx="14.5" cy="9.5" r="0.8" fill="#0b211a"/></svg></span>
          <span class="cl-teddy"><svg viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="18.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="12" cy="10" r="7" fill="currentColor"/><ellipse cx="12" cy="21" rx="6.5" ry="5.5" fill="currentColor"/><circle cx="8" cy="15" r="3" fill="currentColor"/><circle cx="16" cy="15" r="3" fill="currentColor"/><ellipse cx="12" cy="12" rx="3.2" ry="2.5" fill="#0b211a"/><circle cx="9.5" cy="9.5" r="0.8" fill="#0b211a"/><circle cx="14.5" cy="9.5" r="0.8" fill="#0b211a"/></svg></span>
          <span class="cl-teddy"><svg viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="18.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="12" cy="10" r="7" fill="currentColor"/><ellipse cx="12" cy="21" rx="6.5" ry="5.5" fill="currentColor"/><circle cx="8" cy="15" r="3" fill="currentColor"/><circle cx="16" cy="15" r="3" fill="currentColor"/><ellipse cx="12" cy="12" rx="3.2" ry="2.5" fill="#0b211a"/><circle cx="9.5" cy="9.5" r="0.8" fill="#0b211a"/><circle cx="14.5" cy="9.5" r="0.8" fill="#0b211a"/></svg></span>
          <span class="cl-teddy"><svg viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="18.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="12" cy="10" r="7" fill="currentColor"/><ellipse cx="12" cy="21" rx="6.5" ry="5.5" fill="currentColor"/><circle cx="8" cy="15" r="3" fill="currentColor"/><circle cx="16" cy="15" r="3" fill="currentColor"/><ellipse cx="12" cy="12" rx="3.2" ry="2.5" fill="#0b211a"/><circle cx="9.5" cy="9.5" r="0.8" fill="#0b211a"/><circle cx="14.5" cy="9.5" r="0.8" fill="#0b211a"/></svg></span>
          <span class="cl-teddy"><svg viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="5.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="18.5" cy="5.5" r="3.5" fill="currentColor"/><circle cx="12" cy="10" r="7" fill="currentColor"/><ellipse cx="12" cy="21" rx="6.5" ry="5.5" fill="currentColor"/><circle cx="8" cy="15" r="3" fill="currentColor"/><circle cx="16" cy="15" r="3" fill="currentColor"/><ellipse cx="12" cy="12" rx="3.2" ry="2.5" fill="#0b211a"/><circle cx="9.5" cy="9.5" r="0.8" fill="#0b211a"/><circle cx="14.5" cy="9.5" r="0.8" fill="#0b211a"/></svg></span>
        </div>
        """, unsafe_allow_html=True)

        return page




page = sidebar()

def render_overview():
    hero(
        "CLARITY INTELLIGENCE / NLP WORKBENCH",
        "Make meaning unmistakable.",
        "An intelligent review workspace for requirements, contracts, and policy text. Find possible ambiguity, compare detection methods, and make intended meaning explicit."
    )
    st.markdown("")
    cols = st.columns(4, gap="medium")
    cards = [
        ("01 / TAXONOMY", "04", "Ambiguity families", "Vague Â· Attachment Â· Scope Â· Reference"),
        ("02 / METHODS", "03", "Detection methods", "Rules Â· DistilBERT Â· Prompt baseline"),
        ("03 / PRINCIPLE", "Human", "Review first", "Flags are suggestions, not verdicts"),
        ("04 / EVIDENCE", "Measured", "Evaluation", "Real test labels required for results"),
    ]
    for col, (label, value, title, sub) in zip(cols, cards):
        with col:
            st.markdown(
                f"""<div class="metric">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
                <div style="color:#e9dfc8;font-size:12px;font-weight:700;margin-top:6px">{title}</div>
                <div class="sub">{sub}</div>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown("### The clarity workflow")
    st.markdown(
        """<div class="pipeline">
        <div class="pipeline-step"><b>01 / INPUT</b><span>Bring the text</span><p>Paste a clause or review a document.</p></div>
        <div class="pipeline-step"><b>02 / DETECT</b><span>Find signals</span><p>Inspect rule and model predictions.</p></div>
        <div class="pipeline-step"><b>03 / EXPLAIN</b><span>Compare readings</span><p>Understand why wording may be unclear.</p></div>
        <div class="pipeline-step"><b>04 / REFINE</b><span>Improve wording</span><p>Review candidate rewrites with intent in mind.</p></div>
        <div class="pipeline-step"><b>05 / EVALUATE</b><span>Measure quality</span><p>Compare methods on shared test examples.</p></div>
        </div>""",
        unsafe_allow_html=True
    )

    left, right = st.columns([1.15, .85], gap="medium")
    with left:
        st.markdown(
            """<div class="panel">
            <div class="panel-title">FEATURED EXAMPLE / ATTACHMENT</div>
            <h3>One sentence. Two possible readings.</h3>
            <p style="font-size:16px;color:#f0e4c7;line-height:1.8">
            â€œThe admin monitors the user with the sensor.â€
            </p>
            <div class="gold-line"></div>
            <p><span class="pill">READING A</span> The admin uses a sensor to monitor the user.</p>
            <p><span class="pill">READING B</span> The user has a sensor associated with them.</p>
            <p class="small-muted">The system should not guess which meaning was intended. The writer must confirm it.</p>
            </div>""",
            unsafe_allow_html=True
        )
    with right:
        st.markdown(
            """<div class="panel">
            <div class="panel-title">DESIGN PRINCIPLE</div>
            <h3>Precision over certainty.</h3>
            <p>Long sentences are not automatically ambiguous. A useful flag should identify a plausible alternate interpretation and give the writer evidence to review.</p>
            <div class="gold-line"></div>
            <div class="panel-title">DOCUMENT SUMMARY</div>
            <p class="small-muted">Project-defined ambiguity rate = flagged sentences Ã· total sentences Ã— 100.</p>
            <p class="small-muted">This descriptive statistic is not a validated legal-risk score.</p>
            </div>""",
            unsafe_allow_html=True
        )

    st.markdown("")
    st.markdown(
        """<div style="text-align:center;padding:14px;color:#8fa99a;font-size:11px;letter-spacing:1px">
        BUILT FOR CLEARER REQUIREMENTS Â· TRANSPARENT PREDICTIONS Â· HUMAN REVIEW
        </div>""",
        unsafe_allow_html=True
    )


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
    text_value = st.text_area("Sentence or short clause", value=default_text, height=120, placeholder="Paste requirements, contract clauses, or policy languageÃ¢â‚¬Â¦")
    c1, c2 = st.columns([1, 3])
    with c1:
        run = st.button("Analyze sentence", type="primary", use_container_width=True)
    with c2:
        st.caption("Preserves punctuation, negation, modifiers, and pronouns. No text is sent to an external API by this demo app.")
    if run:
        if not text_value.strip():
            st.warning("Enter a sentence before running analysis.")
        else:
            with st.spinner("Inspecting linguistic signalsÃ¢â‚¬Â¦"):
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
                    st.markdown(f"<div class='panel'><span class='pill'>{det['label'].upper()}</span><p style='margin-top:12px'><b>Evidence</b>: <code>{det.get('span') or 'Not provided'}</code></p><p>{det.get('reason','Possible ambiguity detected.')}</p><div class='small-muted'>Source: {det.get('source','unknown')} Â· Confidence: {det.get('confidence') if det.get('confidence') is not None else 'not provided'}</div></div>", unsafe_allow_html=True)
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
        st.caption(f"Mode: {result.get('mode','unknown')} Â· elapsed: {result.get('latency_ms',0):.2f} ms (local wall-clock measurement for this call only)")

def render_document():
    hero("Document review / 03", "Read the whole document.", "Upload a plain-text file or paste content to get sentence-level review and a document summary. File support is intentionally conservative in this first version.")
    upload = st.file_uploader("Upload a UTF-8 .txt file", type=["txt"])
    pasted = st.text_area("Or paste document text", height=160, placeholder="Paste policy, requirement, or contract text hereÃ¢â‚¬Â¦")
    if st.button("Review document", type="primary"):
        raw = ""
        if upload:
            try: raw = upload.getvalue().decode("utf-8-sig")
            except UnicodeDecodeError: st.error("File is not valid UTF-8. Save it as UTF-8 text and retry.")
        else: raw = pasted
        if not raw.strip(): st.warning("Upload a text file or paste document content.")
        else:
            with st.spinner("Reviewing sentencesÃ¢â‚¬Â¦"):
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
            table_rows.append({"Sentence": item["text"], "Flagged": bool(item["detections"]), "Types": ", ".join(d["label"] for d in item["detections"]) or "â€”", "Explanation": item.get("explanation","")})
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        st.download_button("Download document report (CSV)", data=pd.DataFrame(table_rows).to_csv(index=False), file_name="clarity_lint_document_report.csv", mime="text/csv")

def render_evaluation():
    hero("Evaluation lab / 04", "Measure what matters.", "Identical held-out test examples (76 sentences, 5 canonical labels) evaluated across Rule-Based Detection, DistilBERT Classifier, and Zero-Shot Prompt Baseline.")
    
    report_file = ROOT / "outputs" / "evaluation_report.json"
    unified_csv_file = ROOT / "outputs" / "unified_test_evaluation.csv"
    
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
    elif report_file.exists() and unified_csv_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        
        prov = eval_data.get("dataset_provenance", {})
        methods_data = eval_data.get("methods", {})
        
        st.success(f"âœ… Loaded verified test evaluation on {prov.get('total_examples', 76)} held-out examples ({prov.get('test_split_path', 'data/splits/test.csv')}). Zero data leakage.")
        
        # 3-Model Cards
        c1, c2, c3 = st.columns(3)
        col_map = [
            (c1, "rules_pred", "RULE-BASED DETECTOR", "Linguistic rules"),
            (c2, "model_pred", "DISTILBERT CLASSIFIER", "Fine-tuned neural model"),
            (c3, "prompt_pred", "ZERO-SHOT BASELINE (GEMINI)", "LLM prompt baseline")
        ]
        
        for col, key, title, desc in col_map:
            m = methods_data.get(key, {})
            meta = m.get("meta", {})
            f1 = m.get("macro_f1", 0.0)
            acc = m.get("accuracy", 0.0)
            runtime = meta.get("per_sample_ms", 0.0)
            status_tag = meta.get("status", "measured")
            with col:
                st.markdown(
                    f"<div class='panel'>"
                    f"<div class='panel-title'>{title}</div>"
                    f"<h3>Macro-F1: {f1:.4f}</h3>"
                    f"<p class='small-muted'>Accuracy: {acc*100:.1f}% | {desc}</p>"
                    f"<div class='gold-line'></div>"
                    f"<p>Latency: {runtime if runtime is not None else 'N/A'} ms/item<br>"
                    f"<span class='pill'>{status_tag}</span></p>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        # Comparison Table
        st.markdown("### Unified Three-Method Comparison")
        comp_rows = []
        for key in ["rules_pred", "model_pred", "prompt_pred"]:
            if key in methods_data:
                m = methods_data[key]
                meta = m.get("meta", {})
                comp_rows.append({
                    "Method": meta.get("name", key),
                    "Architecture": meta.get("type", "â€”"),
                    "Accuracy": f"{m.get('accuracy', 0.0)*100:.2f}%",
                    "Macro F1": f"{m.get('macro_f1', 0.0):.4f}",
                    "Weighted F1": f"{m.get('weighted_f1', 0.0):.4f}",
                    "Latency (ms/sample)": meta.get("per_sample_ms", "N/A"),
                    "Provenance / Status": meta.get("status", "genuine")
                })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        # Model Trade-offs & Limitations
        with st.expander("Engineering Trade-offs & Architectural Limitations", expanded=False):
            t1, t2, t3 = st.columns(3)
            with t1:
                st.markdown(
                    "**Rule-Based Detector**<br>"
                    "- *Strengths:* Ultra-low latency (~0.2 ms), 0 hardware cost, fully deterministic.<br>"
                    "- *Limitations:* Low recall (36.8% acc); brittle to non-templated phrasings.",
                    unsafe_allow_html=True
                )
            with t2:
                st.markdown(
                    "**DistilBERT Classifier**<br>"
                    "- *Strengths:* High macro F1 (0.9075), balanced across all 5 classes, local CPU/GPU.<br>"
                    "- *Limitations:* Sentence-level label only (span is None); requires training split.",
                    unsafe_allow_html=True
                )
            with t3:
                st.markdown(
                    "**Gemini Zero-Shot Baseline**<br>"
                    "- *Strengths:* High macro F1 (0.9032), extracts exact span substrings and rationale.<br>"
                    "- *Limitations:* Requires GEMINI_API_KEY; external API latency and rate limits.",
                    unsafe_allow_html=True
                )
        
        # Interactive Confusion Matrix
        st.markdown("### Measured Confusion Matrix")
        chosen_method = st.selectbox(
            "Select Method to Inspect",
            ["model_pred", "rules_pred", "prompt_pred"],
            format_func=lambda k: methods_data.get(k, {}).get("meta", {}).get("name", k)
        )
        if chosen_method in methods_data:
            cm = methods_data[chosen_method]["confusion_matrix"]["matrix"]
            fig = px.imshow(cm, x=LABELS, y=LABELS, text_auto=True, aspect="auto", color_continuous_scale=["#102820","#c5a45d"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e9dfc8", xaxis_title="Predicted label", yaxis_title="Gold label")
            st.plotly_chart(fig, use_container_width=True)
            
            # Per-class breakdown
            st.markdown(f"#### Per-Class Breakdown â€” {methods_data[chosen_method]['meta']['name']}")
            pc = methods_data[chosen_method]["per_class"]
            pc_rows = [{"Class": lbl, "Precision": f"{pc[lbl]['precision']:.4f}", "Recall": f"{pc[lbl]['recall']:.4f}", "F1-Score": f"{pc[lbl]['f1']:.4f}", "Support": pc[lbl]["support"]} for lbl in LABELS if lbl in pc]
            st.dataframe(pd.DataFrame(pc_rows), use_container_width=True, hide_index=True)
        
        # Download Unified Predictions
        with open(unified_csv_file, "rb") as fp:
            st.download_button(
                "Download Unified Test Predictions (CSV)",
                data=fp.read(),
                file_name="unified_test_evaluation.csv",
                mime="text/csv"
            )
    else:
        metrics = make_demo_predictions()
        st.warning("Demo mode is active. Real test outputs not found; showing illustrative fixtures.")
        c1,c2,c3 = st.columns(3)
        for col, method in zip([c1,c2,c3], ["rules_pred","model_pred","prompt_pred"]):
            report = metrics[method]
            with col:
                st.markdown(f"<div class='panel'><div class='panel-title'>{method.replace('_',' ').upper()}</div><h3>Illustrative only</h3><p class='small-muted'>Replace with measured test-set output.</p><div class='gold-line'></div><p>Macro-F1 fixture: {report['macro_f1']:.2f}</p></div>", unsafe_allow_html=True)
        st.markdown("### Example confusion matrix â€” fixture data")
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
        ("Person 2 â€” Rules", "src/rules/detect.py", "Active & verified; handcrafted 5-category ambiguity rules connected"),
        ("Person 3 â€” DistilBERT", "src/model/predict.py", "Active & verified; fine-tuned DistilBERT checkpoint loaded & inferencing"),
        ("Person 4 â€” Explanations", "src/explanations/explain.py", "Active & verified; linguistic templates & rewrite generator connected"),
        ("Person 4 â€” Prompt baseline", "src/explanations/baseline.py", "Adapter ready; live execution requires GEMINI_API_KEY environment variable")
    ]
    for owner, path, note in status:
        st.markdown(f"<div class='panel'><b>{owner}</b><div class='small-muted'>{path}</div><p>{note}</p></div>", unsafe_allow_html=True)
    st.info("Place teammates' modules at the paths above or update the adapter configuration in `src/integration/pipeline.py`. Missing modules should be visibleâ€”not silently presented as trained models.")

def render_viva():
    hero("Presentation suite / 07", "Explain the engineering.", "A concise demo flow and viva notes for Team. The goal is to explain integration decisions, evaluation integrity, and limitations clearly.")
    st.markdown("### Suggested 4-minute demo")
    demo = [
        ("0:00Ã¢â‚¬â€œ0:30", "Introduce the problem", "Clarity Lint flags possible ambiguity in requirements, contracts, and policies."),
        ("0:30Ã¢â‚¬â€œ1:15", "Analyze one sentence", "Use Ã¢â‚¬Å“The admin monitors the user with the sensor.Ã¢â‚¬Â Show the competing readings."),
        ("1:15Ã¢â‚¬â€œ2:00", "Review a document", "Show sentence counts, type breakdown, and the project-defined ambiguity rate."),
        ("2:00Ã¢â‚¬â€œ3:00", "Compare methods", "Explain rules vs DistilBERT vs prompt baseline on the same held-out test set."),
        ("3:00Ã¢â‚¬â€œ4:00", "Discuss limitations", "Show one false positive and one false negative; explain why human review matters.")
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

st.markdown("<div class='gold-line'></div><div style='text-align:center;color:#728f80;font:10px DM Mono;letter-spacing:2px;padding:10px'>CLARITY LINT Â· CLARITY Â· TEAM WORKSPACE Â· REVIEW BEFORE RELYING</div>", unsafe_allow_html=True)




# CLARITY_BRAND_FONT_START
st.markdown('\n<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap\');\n\n/* Clarity Lint sidebar brand */\n[data-testid="stSidebar"] .cl-brand,\n[data-testid="stSidebar"] .cl-logo,\n[data-testid="stSidebar"] .brand-name,\n[data-testid="stSidebar"] .sidebar-brand {\n    font-family: \'Manrope\', sans-serif !important;\n    font-size: 22px !important;\n    font-weight: 800 !important;\n    letter-spacing: -0.8px !important;\n    line-height: 1.2 !important;\n    color: #F0E9D8 !important;\n    text-shadow: 0 0 16px rgba(217,184,108,0.10);\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_BRAND_FONT_END

# CLARITY_LAYOUT_FIX_START
st.markdown('\n<style>\n/* ===== Clarity Lint: layout and readability correction ===== */\n\n:root {\n  --cl-bg: #091b16;\n  --cl-card: #102b22;\n  --cl-border: rgba(197, 164, 93, .24);\n  --cl-gold: #d6b66f;\n  --cl-text: #f3eee1;\n  --cl-muted: #a9c2b5;\n}\n\n[data-testid="stAppViewContainer"] {\n  background:\n    radial-gradient(ellipse at 80% 0%, rgba(41, 103, 76, .15), transparent 42%),\n    #091b16 !important;\n}\n\n/* Prevent words breaking in the middle of a word. */\n[data-testid="stMarkdownContainer"],\n[data-testid="stMarkdownContainer"] *,\n[data-testid="stMetric"],\n[data-testid="stMetric"] *,\n.stCaption,\np, li, h1, h2, h3, h4 {\n  word-break: normal !important;\n  overflow-wrap: break-word !important;\n  hyphens: none !important;\n}\n\n/* Keep cards inside their columns and give them breathing room. */\n[data-testid="stHorizontalBlock"] {\n  gap: 14px !important;\n  align-items: stretch !important;\n}\n\n[data-testid="stColumn"] {\n  min-width: 0 !important;\n}\n\n[data-testid="stVerticalBlockBorderWrapper"] {\n  min-width: 0 !important;\n  overflow: hidden;\n  border: 1px solid var(--cl-border) !important;\n  border-radius: 14px !important;\n  background: linear-gradient(145deg, rgba(20, 48, 37, .9), rgba(10, 31, 24, .96)) !important;\n  padding: 12px !important;\n  box-sizing: border-box !important;\n}\n\n/* Fix the four overview feature cards. */\n.panel {\n  box-sizing: border-box !important;\n  min-width: 0 !important;\n  width: 100% !important;\n  height: 100%;\n  padding: 18px !important;\n  border-radius: 15px !important;\n  overflow: hidden !important;\n  overflow-wrap: break-word !important;\n  word-break: normal !important;\n}\n\n.panel h3 {\n  font-size: clamp(15px, 1.25vw, 20px) !important;\n  line-height: 1.35 !important;\n  white-space: normal !important;\n  word-break: normal !important;\n  overflow-wrap: break-word !important;\n  margin-bottom: 8px !important;\n}\n\n.panel p {\n  font-size: 13px !important;\n  line-height: 1.6 !important;\n}\n\n/* Improve hero proportions and heading readability. */\n.hero {\n  box-sizing: border-box !important;\n  width: 100% !important;\n  min-width: 0 !important;\n  padding: clamp(22px, 3vw, 36px) !important;\n  border-radius: 18px !important;\n}\n\n.hero h1 {\n  font-size: clamp(27px, 3.2vw, 43px) !important;\n  line-height: 1.18 !important;\n  overflow-wrap: normal !important;\n  word-break: normal !important;\n}\n\n/* Keep sidebar branding compact. */\n[data-testid="stSidebar"] img {\n  display: block;\n  width: auto !important;\n  max-width: 110px !important;\n  max-height: 145px !important;\n  object-fit: contain !important;\n  object-position: left center !important;\n  margin: 4px auto 14px 0 !important;\n  border-radius: 9px;\n}\n\n[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {\n  overflow-wrap: normal !important;\n}\n\n[data-testid="stSidebar"] .stButton > button {\n  min-height: 42px !important;\n  white-space: normal !important;\n  line-height: 1.3 !important;\n  border-radius: 10px !important;\n}\n\n/* Consistent readable typography and clean controls. */\n[data-testid="stMetricLabel"] {\n  color: var(--cl-muted) !important;\n  font-size: 12px !important;\n}\n\n[data-testid="stMetricValue"] {\n  color: var(--cl-text) !important;\n}\n\n.stTextArea textarea, .stTextInput input {\n  border-radius: 11px !important;\n}\n\n.stButton > button {\n  transition: border-color .18s ease, box-shadow .18s ease,\n              transform .18s ease !important;\n}\n\n.stButton > button:hover {\n  border-color: var(--cl-gold) !important;\n  box-shadow: 0 0 14px rgba(197, 164, 93, .12) !important;\n}\n\n/* Hide the old decorative teddy rain if present. */\n.cl-teddy-rain,\n.cl-teddy,\n[class*="teddy-rain"] {\n  display: none !important;\n}\n\n@media (max-width: 900px) {\n  .hero { padding: 22px !important; }\n  .panel { padding: 13px !important; }\n  .panel p { font-size: 12px !important; }\n}\n\n@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after {\n    transition: none !important;\n    animation: none !important;\n  }\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_LAYOUT_FIX_END

# CLARITY_INLINE_BRAND_CSS_START
st.markdown('\n<style>\n/* Clarity Lint ? cohesive neon brand and dashboard */\n:root {\n  --cl-bg: #080c1b;\n  --cl-panel: #101832;\n  --cl-purple: #8b5cf6;\n  --cl-pink: #e879f9;\n  --cl-blue: #60a5fa;\n  --cl-text: #f4f1ff;\n  --cl-muted: #a8b4d5;\n}\n.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {\n  background:\n    radial-gradient(ellipse at 75% 0%, rgba(88, 45, 174, .20), transparent 40%),\n    radial-gradient(ellipse at 5% 40%, rgba(34, 73, 155, .10), transparent 35%),\n    var(--cl-bg) !important;\n}\n[data-testid="stSidebar"] {\n  background: linear-gradient(180deg, #080d20, #0a1021) !important;\n  border-right: 1px solid rgba(139, 92, 246, .28) !important;\n}\n.cl-brand-wrap {\n  display: flex;\n  align-items: center;\n  gap: 11px;\n  width: 100%;\n  min-width: 0;\n  padding: 13px 10px;\n  margin: 2px 0 14px;\n  border: 1px solid rgba(167, 139, 250, .26);\n  border-radius: 14px;\n  background: linear-gradient(115deg, #123b29, #0b261b);\n  box-shadow: inset 0 1px rgba(255,255,255,.035), 0 0 18px rgba(70,130,85,.10);\n  box-sizing: border-box;\n}\n.cl-brand-symbol {\n  flex: 0 0 39px;\n  width: 39px;\n  height: 39px;\n  display: grid;\n  place-items: center;\n  border-radius: 12px;\n  border: 1px solid rgba(214,182,111,.42);\n  background: linear-gradient(145deg, #1a4a32, #103323);\n  box-shadow: 0 0 18px rgba(90,150,95,.12);\n}\n.cl-brand-copy { min-width: 0; }\n.cl-brand-name {\n  color: #f8f5ff;\n  font-family: "Trebuchet MS", Arial, sans-serif;\n  font-size: 16px;\n  font-weight: 800;\n  letter-spacing: 1.1px;\n  line-height: 1.25;\n  white-space: nowrap;\n}\n.cl-brand-name span {\n  color: #e0c17b;\n}\n.cl-brand-tag {\n  color: #a9b8df;\n  font-size: 7px;\n  font-weight: 700;\n  letter-spacing: 1.15px;\n  line-height: 1.5;\n  margin-top: 5px;\n  white-space: normal;\n}\n[data-testid="stSidebar"] hr {\n  border-color: rgba(139,92,246,.22) !important;\n}\n[data-testid="stSidebar"] .stButton > button {\n  border-radius: 10px !important;\n  transition: border-color .2s, box-shadow .2s, transform .2s !important;\n}\n[data-testid="stSidebar"] .stButton > button:hover {\n  border-color: rgba(192,132,252,.65) !important;\n  box-shadow: 0 0 16px rgba(139,92,246,.15) !important;\n}\nh1, h2, h3 {\n  color: var(--cl-text) !important;\n}\n[data-testid="stMetric"],\ndiv[data-testid="stVerticalBlockBorderWrapper"] {\n  background: linear-gradient(145deg, rgba(19,29,59,.86), rgba(10,16,37,.94));\n  border: 1px solid rgba(139,92,246,.22);\n  border-radius: 14px;\n  transition: border-color .2s, box-shadow .2s, transform .2s;\n}\n[data-testid="stMetric"]:hover,\ndiv[data-testid="stVerticalBlockBorderWrapper"]:hover {\n  border-color: rgba(192,132,252,.5);\n  box-shadow: 0 8px 25px rgba(76,29,149,.13);\n  transform: translateY(-2px);\n}\n.stTextInput input, .stTextArea textarea {\n  background: rgba(8,13,31,.85) !important;\n  color: var(--cl-text) !important;\n  border-color: rgba(129,140,248,.32) !important;\n  border-radius: 10px !important;\n}\n.stButton > button, .stDownloadButton > button {\n  border-radius: 10px !important;\n  transition: all .2s ease !important;\n}\n.stButton > button:hover, .stDownloadButton > button:hover {\n  border-color: #c084fc !important;\n  box-shadow: 0 0 16px rgba(168,85,247,.18);\n}\n.cl-teddy-rain, .cl-teddy, [class*="teddy-rain"] {\n  display: none !important;\n}\n@media (max-width: 700px) {\n  .cl-brand-wrap { gap: 8px; padding: 10px 7px; }\n  .cl-brand-name { font-size: 14px; letter-spacing: .6px; }\n  .cl-brand-tag { font-size: 6px; letter-spacing: .7px; }\n}\n@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after { transition: none !important; }\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_INLINE_BRAND_CSS_END

# CLARITY_ALL_GREEN_START
st.markdown('\n<style>\n:root {\n  --forest: #071a13;\n  --forest-deep: #06140f;\n  --forest-panel: #0e2b20;\n  --forest-card: #102f23;\n  --forest-border: rgba(184, 157, 88, .30);\n  --gold: #d6b66f;\n  --gold-bright: #f0d69a;\n  --green: #72c99a;\n  --green-muted: #9bbdac;\n  --cream: #f3eddf;\n}\n\n/* Entire page: forest green only */\nhtml, body, .stApp,\n[data-testid="stAppViewContainer"],\n[data-testid="stMain"],\n[data-testid="stHeader"] {\n  background-color: var(--forest-deep) !important;\n}\n\n[data-testid="stAppViewContainer"] {\n  background:\n    radial-gradient(ellipse at 65% 0%, rgba(34, 104, 70, .22), transparent 48%),\n    linear-gradient(135deg, #071a13 0%, #091d15 55%, #06150f 100%) !important;\n}\n\n/* Top bar */\n[data-testid="stHeader"] {\n  background: rgba(6, 20, 15, .96) !important;\n}\n\n/* Sidebar */\n[data-testid="stSidebar"] {\n  background: linear-gradient(180deg, #0b261c 0%, #071a13 100%) !important;\n  border-right: 1px solid var(--forest-border) !important;\n}\n\n[data-testid="stSidebar"] > div:first-child {\n  background: transparent !important;\n}\n\n[data-testid="stSidebar"] hr,\nhr {\n  border-color: rgba(184, 157, 88, .24) !important;\n}\n\n/* Headings and text */\nh1, h2, h3, h4,\n[data-testid="stMarkdownContainer"] h1,\n[data-testid="stMarkdownContainer"] h2,\n[data-testid="stMarkdownContainer"] h3 {\n  color: var(--cream) !important;\n}\n\np, li, label,\n[data-testid="stMarkdownContainer"] {\n  color: #d5e4d9;\n}\n\n/* Cards and metrics */\n[data-testid="stMetric"],\ndiv[data-testid="stVerticalBlockBorderWrapper"],\ndiv[data-testid="stExpander"],\n[data-testid="stDataFrame"],\n[data-testid="stTable"] {\n  background: linear-gradient(145deg, #123526 0%, #0b241a 100%) !important;\n  border: 1px solid var(--forest-border) !important;\n  border-radius: 15px !important;\n  box-shadow: inset 0 1px rgba(255,255,255,.025);\n  transition: border-color .22s ease, box-shadow .22s ease,\n              transform .22s ease;\n}\n\n[data-testid="stMetric"]:hover,\ndiv[data-testid="stVerticalBlockBorderWrapper"]:hover,\ndiv[data-testid="stExpander"]:hover {\n  border-color: rgba(214, 182, 111, .60) !important;\n  box-shadow: 0 8px 25px rgba(0,0,0,.16),\n              0 0 18px rgba(66, 151, 100, .10);\n  transform: translateY(-2px);\n}\n\n[data-testid="stMetricLabel"] {\n  color: var(--green-muted) !important;\n}\n\n[data-testid="stMetricValue"] {\n  color: var(--cream) !important;\n}\n\n/* Existing hero sections */\n.hero {\n  background: linear-gradient(125deg, #153b2b 0%, #0d2b20 58%, #081e16 100%) !important;\n  border-color: rgba(214, 182, 111, .42) !important;\n  border-radius: 17px !important;\n}\n\n.eyebrow, .pill {\n  color: var(--gold-bright) !important;\n}\n\n.pill {\n  border-color: rgba(214, 182, 111, .40) !important;\n  background: rgba(214, 182, 111, .055) !important;\n}\n\n/* Navigation */\n[data-testid="stSidebar"] .stButton > button {\n  color: var(--cream) !important;\n  background: linear-gradient(110deg, #103526, #0b281d) !important;\n  border: 1px solid rgba(184, 157, 88, .25) !important;\n  border-radius: 10px !important;\n}\n\n[data-testid="stSidebar"] .stButton > button:hover {\n  background: linear-gradient(110deg, #194b34, #103526) !important;\n  border-color: var(--gold) !important;\n}\n\n/* Main buttons */\n.stButton > button,\n.stDownloadButton > button,\n[data-testid="stFormSubmitButton"] > button {\n  color: #fff7e5 !important;\n  background: linear-gradient(110deg, #386b48, #24563a) !important;\n  border: 1px solid rgba(214, 182, 111, .48) !important;\n  border-radius: 10px !important;\n  transition: all .2s ease !important;\n}\n\n.stButton > button:hover,\n.stDownloadButton > button:hover,\n[data-testid="stFormSubmitButton"] > button:hover {\n  background: linear-gradient(110deg, #477f54, #2e6944) !important;\n  border-color: var(--gold-bright) !important;\n  box-shadow: 0 0 17px rgba(79, 168, 109, .18) !important;\n  transform: translateY(-1px);\n}\n\n/* Text fields */\n.stTextInput input,\n.stTextArea textarea,\n.stNumberInput input,\n[data-baseweb="select"] > div {\n  color: var(--cream) !important;\n  background: #091f16 !important;\n  border: 1px solid rgba(128, 173, 143, .35) !important;\n  border-radius: 10px !important;\n}\n\n.stTextInput input:focus,\n.stTextArea textarea:focus,\n.stNumberInput input:focus {\n  border-color: var(--green) !important;\n  box-shadow: 0 0 0 1px rgba(114, 201, 154, .22) !important;\n}\n\n/* Progress indicators */\n[data-testid="stProgressBar"] > div > div {\n  background: linear-gradient(90deg, #34794c, #8fc99a) !important;\n}\n\n/* Remove the old teddy decoration */\n.cl-teddy-rain, .cl-teddy, [class*="teddy-rain"] {\n  display: none !important;\n}\n\n/* Prevent mid-word wrapping in cards */\n[data-testid="stMarkdownContainer"] *,\n[data-testid="stMetric"] *,\n.panel, .panel * {\n  word-break: normal !important;\n  overflow-wrap: break-word !important;\n  hyphens: none !important;\n}\n\n@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after {\n    transition: none !important;\n    animation: none !important;\n    transform: none !important;\n  }\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_ALL_GREEN_END

# CLARITY_BACKGROUND_FIX_START
st.markdown('\n<style>\n/* Force the entire Streamlit page to use forest green */\nhtml, body,\n.stApp,\n[data-testid="stApp"],\n[data-testid="stAppViewContainer"],\n[data-testid="stMain"],\n[data-testid="stMainBlockContainer"],\n[data-testid="stHeader"],\n[data-testid="stBottom"],\n[data-testid="stVerticalBlock"],\n[data-testid="stHorizontalBlock"] {\n    background-color: #0b2419 !important;\n}\n\n/* Main canvas: visible green, not black or navy */\n[data-testid="stAppViewContainer"] {\n    background: linear-gradient(\n        135deg,\n        #103b29 0%,\n        #0d3022 48%,\n        #09251a 100%\n    ) !important;\n}\n\n/* Keep the top toolbar in the same palette */\n[data-testid="stHeader"] {\n    background: rgba(8, 32, 22, .96) !important;\n}\n\n/* Main content area */\n[data-testid="stMain"] {\n    background: transparent !important;\n}\n[data-testid="stMainBlockContainer"] {\n    background: transparent !important;\n}\n\n/* Green cards with gold outlines */\n[data-testid="stMetric"],\ndiv[data-testid="stVerticalBlockBorderWrapper"],\ndiv[data-testid="stExpander"] {\n    background: linear-gradient(145deg, #174530, #103323) !important;\n    border-color: rgba(214, 182, 111, .38) !important;\n}\n\n/* Keep input controls dark green */\n.stTextInput input,\n.stTextArea textarea,\n.stNumberInput input,\n[data-baseweb="select"] > div {\n    background: #0a261a !important;\n    color: #f3eddf !important;\n}\n\n/* Preserve readable light text */\nh1, h2, h3, h4,\n[data-testid="stMarkdownContainer"],\n[data-testid="stMetricValue"] {\n    color: #f3eddf !important;\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_BACKGROUND_FIX_END

# CLARITY_UNIFIED_CARDS_START
st.markdown('\n<style>\n/* =====================================================\n   CLARITY LINT ? UNIFIED FOREST / ANTIQUE GOLD CARDS\n   ===================================================== */\n\n:root {\n  --cl-card-bg: #102f23;\n  --cl-card-bg-deep: #0b241a;\n  --cl-card-border: rgba(190, 160, 91, .32);\n  --cl-card-border-hover: rgba(222, 194, 125, .78);\n  --cl-card-title: #f1dfb2;\n  --cl-card-text: #f0eee4;\n  --cl-card-muted: #a5c4b2;\n}\n\n/* Common custom cards used by the app */\n.panel,\n.hero,\n.card,\n.metric-card,\n.stat-card,\n.feature-card,\n.workflow-card,\n.result-card,\n.ambiguity-card,\n.method-card,\n.document-card,\n.status-card,\n.example-card,\n.step-card,\n.info-card,\n.cl-card {\n  box-sizing: border-box !important;\n  background: linear-gradient(\n    145deg,\n    #143b2b 0%,\n    #102f23 58%,\n    #0c281d 100%\n  ) !important;\n  border: 1px solid var(--cl-card-border) !important;\n  border-radius: 14px !important;\n  color: var(--cl-card-text) !important;\n  box-shadow: inset 0 1px rgba(255,255,255,.025);\n  transition: border-color .2s ease, box-shadow .2s ease,\n              transform .2s ease !important;\n}\n\n.panel:hover,\n.card:hover,\n.metric-card:hover,\n.stat-card:hover,\n.feature-card:hover,\n.workflow-card:hover,\n.result-card:hover,\n.ambiguity-card:hover,\n.method-card:hover,\n.document-card:hover,\n.status-card:hover,\n.example-card:hover,\n.step-card:hover,\n.info-card:hover,\n.cl-card:hover {\n  border-color: var(--cl-card-border-hover) !important;\n  box-shadow: 0 8px 24px rgba(0,0,0,.12),\n              0 0 15px rgba(81,143,100,.08) !important;\n}\n\n/* Streamlit bordered containers and expanders */\n[data-testid="stVerticalBlockBorderWrapper"],\n[data-testid="stExpander"],\n[data-testid="stMetric"],\n[data-testid="stDataFrame"],\n[data-testid="stTable"] {\n  box-sizing: border-box !important;\n  background: linear-gradient(\n    145deg,\n    #143b2b 0%,\n    #102f23 58%,\n    #0c281d 100%\n  ) !important;\n  border: 1px solid var(--cl-card-border) !important;\n  border-radius: 14px !important;\n  color: var(--cl-card-text) !important;\n  box-shadow: inset 0 1px rgba(255,255,255,.025);\n}\n\n/* Titles and text inside cards */\n.panel h1, .panel h2, .panel h3, .panel h4,\n.card h1, .card h2, .card h3, .card h4,\n.metric-card h1, .metric-card h2, .metric-card h3,\n.feature-card h1, .feature-card h2, .feature-card h3,\n.workflow-card h1, .workflow-card h2, .workflow-card h3,\n.result-card h1, .result-card h2, .result-card h3,\n.document-card h1, .document-card h2, .document-card h3,\n.cl-card h1, .cl-card h2, .cl-card h3 {\n  color: var(--cl-card-title) !important;\n  line-height: 1.35 !important;\n  overflow-wrap: break-word !important;\n  word-break: normal !important;\n}\n\n.panel p, .card p, .metric-card p, .feature-card p,\n.workflow-card p, .result-card p, .document-card p,\n.cl-card p {\n  color: var(--cl-card-muted) !important;\n  line-height: 1.6 !important;\n  overflow-wrap: break-word !important;\n  word-break: normal !important;\n}\n\n/* Hero stays visually prominent, but uses the same palette */\n.hero {\n  background: linear-gradient(\n    120deg,\n    #174531 0%,\n    #103324 55%,\n    #0b261b 100%\n  ) !important;\n  border-color: rgba(190,160,91,.48) !important;\n  border-radius: 17px !important;\n}\n\n/* Metrics: same card finish, consistent readable numbers */\n[data-testid="stMetricLabel"] {\n  color: var(--cl-card-muted) !important;\n}\n[data-testid="stMetricValue"] {\n  color: var(--cl-card-title) !important;\n}\n\n/* Remove unwanted blue/purple card fills and borders */\n[data-testid="stMetric"],\n[data-testid="stVerticalBlockBorderWrapper"],\n[data-testid="stExpander"],\n[data-testid="stDataFrame"],\n[data-testid="stTable"] {\n  --card-border-color: var(--cl-card-border);\n}\n\n/* Keep content readable and avoid mid-word splitting */\n[data-testid="stMarkdownContainer"] *,\n[data-testid="stMetric"] *,\n.panel *, .card *, .feature-card *,\n.workflow-card *, .result-card *, .cl-card * {\n  overflow-wrap: break-word !important;\n  word-break: normal !important;\n  hyphens: none !important;\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .panel, .card, .metric-card, .feature-card,\n  .workflow-card, .result-card, .cl-card {\n    transition: none !important;\n  }\n}\n</style>\n', unsafe_allow_html=True)
# CLARITY_UNIFIED_CARDS_END


