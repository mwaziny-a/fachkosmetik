import streamlit as st
import requests
import io
import os
from PIL import Image

DEFAULT_ANALYZE_URLS = [
    "http://127.0.0.1:8000/api/v1/analyze",
    "http://localhost:8000/api/v1/analyze",
]


def build_api_candidates() -> list:
    candidates = []
    try:
        configured_url = st.secrets["API_URL"]
    except Exception:
        configured_url = os.environ.get("API_URL", "")

    if configured_url:
        candidates.append(configured_url.rstrip("/"))

    for url in DEFAULT_ANALYZE_URLS:
        if url not in candidates:
            candidates.append(url)

    return candidates


API_CANDIDATES = build_api_candidates()
API_URL = API_CANDIDATES[0]

st.set_page_config(
    page_title="FaceInsight AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0d0d0d; color: #e8e2d9; }
  .main .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1100px; }
  h1,h2,h3 { font-family: 'Cormorant Garamond', serif; }
  .hero-title { font-family: 'Cormorant Garamond', serif; font-size: 3.8rem; font-weight: 300; letter-spacing: 0.12em; color: #e8e2d9; text-transform: uppercase; line-height: 1; margin-bottom: 0.2rem; }
  .hero-sub { font-size: 0.85rem; font-weight: 300; letter-spacing: 0.25em; color: #8a7f72; text-transform: uppercase; margin-bottom: 3rem; }
  .thin-rule { border: none; border-top: 1px solid #2a2a2a; margin: 2rem 0; }
  .section-label { font-size: 0.7rem; font-weight: 500; letter-spacing: 0.3em; text-transform: uppercase; color: #c9b99a; margin-bottom: 1rem; margin-top: 2rem; }
  .summary-card { background: #161616; border: 1px solid #2a2a2a; border-left: 3px solid #c9b99a; padding: 1.5rem 2rem; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.7; color: #d4ccc2; }
  .rec-card { background: #131313; border: 1px solid #222; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; }
  .rec-title { font-family: 'Cormorant Garamond', serif; font-size: 1.15rem; font-weight: 500; color: #e8e2d9; margin-bottom: 0.3rem; }
  .rec-desc { font-size: 0.88rem; color: #9a9188; line-height: 1.6; margin-bottom: 0.5rem; }
  .rec-impact { font-size: 0.78rem; color: #c9b99a; font-style: italic; }
  .rec-notes { font-size: 0.78rem; color: #6a6058; margin-top: 0.3rem; }
  .badge { display: inline-block; font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase; padding: 0.15rem 0.5rem; margin-right: 0.4rem; border: 1px solid #2a2a2a; color: #6a6058; margin-bottom: 0.5rem; }
  .badge-none { border-color: #2a4a2a; color: #5a9a5a; }
  .badge-low { border-color: #2a3a4a; color: #5a8aaa; }
  .badge-medium { border-color: #4a3a2a; color: #aa8a5a; }
  .badge-high { border-color: #4a2a2a; color: #aa5a5a; }
  .badge-specialist { border-color: #3a2a4a; color: #8a5aaa; }
  .analysis-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin: 1rem 0; }
  .analysis-cell { background: #131313; border: 1px solid #222; padding: 1rem 1.2rem; }
  .cell-label { font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; color: #5a5248; margin-bottom: 0.4rem; }
  .cell-value { font-size: 0.9rem; color: #c9c3bb; line-height: 1.4; }
  .concern-item { padding: 0.4rem 0; border-bottom: 1px solid #1a1a1a; font-size: 0.88rem; color: #9a9188; }
  .prominent-tag { display: inline-block; border: 1px solid #2a2a2a; padding: 0.2rem 0.6rem; margin: 0.2rem; font-size: 0.75rem; color: #8a7f72; }
  .warning-card { background: #1a1008; border: 1px solid #3a2a10; border-left: 3px solid #aa6a20; padding: 1rem 1.5rem; margin-bottom: 0.8rem; font-size: 0.88rem; color: #c09060; line-height: 1.6; }
  .disclaimer { background: #0f0f0f; border: 1px solid #1e1e1e; padding: 1.2rem 1.5rem; font-size: 0.78rem; color: #5a5248; line-height: 1.6; margin-top: 3rem; font-style: italic; }
  .quality-bar-bg { background: #1a1a1a; height: 4px; width: 100%; margin-top: 0.5rem; }
  .quality-bar-fill { height: 4px; background: linear-gradient(90deg, #c9b99a, #8a7f72); }
  [data-testid="stFileUploader"] { background: #111 !important; border: 1px dashed #2a2a2a !important; border-radius: 0 !important; }
  .stButton > button { background: #c9b99a !important; color: #0d0d0d !important; border: none !important; border-radius: 0 !important; font-size: 0.78rem !important; letter-spacing: 0.2em !important; text-transform: uppercase !important; padding: 0.75rem 2.5rem !important; font-weight: 500 !important; }
  .stButton > button:hover { background: #e8d8b8 !important; }
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── session_state init ─────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None
if "analyzing" not in st.session_state:
    st.session_state.analyzing = False


# ── helpers ────────────────────────────────────────────────────────────────────
LEVEL_LABEL = {
    "none": "No intervention", "low": "Low effort",
    "medium": "Moderate", "high": "High", "specialist": "Specialist only",
}


def render_rec_card(item: dict) -> None:
    level = item.get("intervention_level", "low")
    label = LEVEL_LABEL.get(level, level.title())
    notes_html = f'<div class="rec-notes">↳ {item["notes"]}</div>' if item.get("notes") else ""
    st.markdown(
        f'<div class="rec-card">'
        f'<div><span class="badge">#{item.get("priority","–")}</span>'
        f'<span class="badge badge-{level}">{label}</span></div>'
        f'<div class="rec-title">{item.get("title","")}</div>'
        f'<div class="rec-desc">{item.get("description","")}</div>'
        f'<div class="rec-impact">→ {item.get("estimated_impact","")}</div>'
        f'{notes_html}</div>',
        unsafe_allow_html=True,
    )


def render_section(label: str, items: list, preamble: str = "") -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    if preamble:
        st.markdown(
            f'<div class="rec-desc" style="color:#6a6058;margin-bottom:1rem;">{preamble}</div>',
            unsafe_allow_html=True,
        )
    if not items:
        st.markdown(
            '<div class="rec-desc" style="color:#3a3530;padding:0.5rem 0;">No recommendations in this area.</div>',
            unsafe_allow_html=True,
        )
        return
    for item in items:
        render_rec_card(item)


def render_analysis_grid(report: dict) -> None:
    skin = report.get("skin_analysis", {})
    face = report.get("face_structure", {})
    eye  = report.get("eye_analysis", {})
    cells = [
        ("Skin Tone",   skin.get("skin_tone", "—")),
        ("Texture",     skin.get("apparent_texture", "—")),
        ("Hydration",   skin.get("hydration_assessment", "—")),
        ("Face Shape",  face.get("face_shape", "—")),
        ("Symmetry",    face.get("symmetry_notes", "—")),
        ("Proportions", face.get("proportions_note", "—")),
        ("Eye Shape",   eye.get("eye_shape", "—")),
        ("Eye Spacing", eye.get("eye_spacing", "—")),
        ("Brow",        f"{eye.get('brow_shape','—')} · {eye.get('brow_density','—')}"),
    ]
    html = '<div class="analysis-grid">'
    for lbl, val in cells:
        html += (
            f'<div class="analysis-cell">'
            f'<div class="cell-label">{lbl}</div>'
            f'<div class="cell-value">{val}</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    for c in skin.get("visible_concerns", []):
        st.markdown(f'<div class="concern-item">· {c}</div>', unsafe_allow_html=True)

    prominent = face.get("prominent_features", [])
    if prominent:
        tags = "".join(f'<span class="prominent-tag">{f}</span>' for f in prominent)
        st.markdown(tags, unsafe_allow_html=True)


def show_report(result: dict) -> None:
    report  = result.get("report", {})
    quality = result.get("quality_check", {})

    pct = int(quality.get("score", 1.0) * 100)
    st.markdown(
        f'<div style="margin:0.5rem 0 2rem 0;">'
        f'<span class="cell-label">Image Quality — {pct}%</span>'
        f'<div class="quality-bar-bg"><div class="quality-bar-fill" style="width:{pct}%;"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="section-label">Overview</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="summary-card">{report.get("summary","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-label">Facial Analysis</div>', unsafe_allow_html=True)
    render_analysis_grid(report)
    st.markdown('<hr class="thin-rule">', unsafe_allow_html=True)

    tabs = st.tabs([
        "Skincare", "Grooming", "Hairstyle", "Beard",
        "Makeup", "Non-Invasive", "Injectables", "Procedural", "Avoid",
    ])
    with tabs[0]: render_section("Skincare Protocol",    report.get("skincare_recommendations", []))
    with tabs[1]: render_section("Grooming Direction",   report.get("grooming_recommendations", []))
    with tabs[2]: render_section("Hairstyle Guidance",   report.get("hairstyle_recommendations", []))
    with tabs[3]: render_section("Beard Guidance",       report.get("beard_recommendations", []))
    with tabs[4]: render_section("Makeup Techniques",    report.get("makeup_recommendations", []))
    with tabs[5]: render_section("Non-Invasive Options", report.get("non_invasive_options", []))
    with tabs[6]: render_section(
        "Injectables to Discuss", report.get("injectables_to_discuss", []),
        preamble="Discuss with a qualified injector or aesthetic physician only.",
    )
    with tabs[7]: render_section(
        "Procedural Consultations", report.get("procedural_surgical_consultation", []),
        preamble="Explore only with a board-certified surgeon or specialist.",
    )
    with tabs[8]:
        st.markdown('<div class="section-label">What Not To Do</div>', unsafe_allow_html=True)
        for item in report.get("what_not_to_do", []):
            st.markdown(f'<div class="warning-card">✕ {item}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="disclaimer">{report.get("disclaimer","")}</div>', unsafe_allow_html=True)
    with st.expander("Raw JSON Output"):
        st.json(result.get("raw_json", {}))


def do_analysis(image_bytes: bytes, filename: str) -> None:
    """Called on button click. Stores result in session_state."""
    resp = None
    result = {}
    status = 0

    for url in API_CANDIDATES:
        try:
            resp = requests.post(
                url,
                files={"file": (filename, image_bytes, "image/jpeg")},
                timeout=120,
            )
            result = resp.json()
            status = resp.status_code
            break
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            st.session_state.error_msg = "Request timed out. Please try again."
            st.session_state.result = None
            return
        except Exception as e:
            st.session_state.error_msg = f"Unexpected error: {e}"
            st.session_state.result = None
            return

    if resp is None:
        st.session_state.error_msg = (
            "Cannot connect to the backend. "
            "Make sure FastAPI is running on port 8000, or set API_URL in Streamlit secrets."
        )
        st.session_state.result = None
        return

    if status != 200:
        err = result.get("error", result)
        if isinstance(err, dict) and "issues" in err:
            st.session_state.error_msg = "quality_fail:" + "|".join(err.get("issues", []))
        else:
            st.session_state.error_msg = f"Error {status}: {err}"
        st.session_state.result = None
        return

    st.session_state.result = result
    st.session_state.error_msg = None


# ── page ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">FaceInsight</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">AI Cosmetic Analysis · Confidential · Instant</div>', unsafe_allow_html=True)
st.markdown('<hr class="thin-rule">', unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1])

with col_left:
    st.markdown('<div class="section-label">Upload your photo</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rec-desc" style="margin-bottom:1rem;">'
        'Clear, well-lit frontal portrait. Single face. No sunglasses or heavy filters.'
        '</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Choose image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

with col_right:
    st.markdown('<div class="section-label">What you get</div>', unsafe_allow_html=True)
    for item in [
        "Skin & texture deep-dive",
        "Face structure breakdown",
        "Prioritized skincare protocol",
        "Grooming & hairstyle direction",
        "Non-invasive options ranked",
        "Injectable & procedural guidance",
        "Specific things to avoid",
    ]:
        st.markdown(f'<div class="rec-desc">· {item}</div>', unsafe_allow_html=True)

# ── upload handling ────────────────────────────────────────────────────────────
if uploaded is not None:

    try:
        img = Image.open(uploaded)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=92)
        img_bytes = buf.getvalue()
    except Exception as e:
        st.error(f"Could not read image: {e}")
        st.stop()

    st.markdown('<hr class="thin-rule">', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(img)
    with c2:
        st.markdown('<div class="section-label">Ready</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="rec-desc" style="margin-bottom:1.5rem;">'
            'Processed securely. Analysis takes 15–30 seconds.'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run Analysis →"):
            st.session_state.result = None
            st.session_state.error_msg = None
            with st.spinner("Analyzing…"):
                do_analysis(img_bytes, uploaded.name)

    st.markdown('<hr class="thin-rule">', unsafe_allow_html=True)

    if st.session_state.error_msg:
        msg = st.session_state.error_msg
        if msg.startswith("quality_fail:"):
            st.error("Image quality check failed.")
            for issue in msg.replace("quality_fail:", "").split("|"):
                st.markdown(f'<div class="warning-card">⚠ {issue}</div>', unsafe_allow_html=True)
        else:
            st.error(msg)

    if st.session_state.result is not None:
        show_report(st.session_state.result)

else:
    st.session_state.result = None
    st.session_state.error_msg = None
    st.markdown(
        '<div style="margin-top:4rem;text-align:center;">'
        '<div style="font-family:\'Cormorant Garamond\',serif;font-size:4rem;font-weight:300;color:#2a2a2a;">✦</div>'
        '<div style="font-size:0.75rem;letter-spacing:0.3em;text-transform:uppercase;color:#2a2520;">'
        'Upload an image to begin'
        '</div></div>',
        unsafe_allow_html=True,
    )