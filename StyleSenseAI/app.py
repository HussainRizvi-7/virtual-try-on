import os
import io
import subprocess
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Local Imports
from ui_styles import css
from cv_analyzer import analyze_outfit
from recommender import generate_three_outfit_recommendations
from ootd_tryon import check_ootd_status, run_ootd_tryon
from llm_advisor import check_gemini_status, generate_llm_fashion_advice, answer_fashion_chat
load_dotenv()

GENDERS = ["Neutral", "Male", "Female"]
WEATHER = ["Normal", "Hot", "Cold", "Rainy"]

st.set_page_config(
    page_title="StyleSense AI",
    page_icon="*",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(css, unsafe_allow_html=True)

# Session State Initialization
_defaults = {
    "uploaded_bytes": None,
    "uploaded_img": None,
    "cloth_bytes": None,
    "cloth_img": None,
    "analysis_data": None,
    "outfit_ideas": None,
    "tryon_image": None,
    "llm_advice": None,
    "chat_history": []
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Sidebar
st.sidebar.markdown("<h2>* StyleSense AI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#a39bb8; margin-top:-15px;'>Intelligent Fashion Assistant</p>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Preferences")
user_gender = st.sidebar.selectbox("Gender Focus", GENDERS, index=0)
user_weather = st.sidebar.selectbox("Weather Condition", WEATHER, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### API Status")

ootd_status = check_ootd_status()
gem_status = check_gemini_status()

ootd_label = "Ready" if ootd_status["ready"] else "Not found"
st.sidebar.markdown(f"OOTDiffusion: **{ootd_label}**")
st.sidebar.markdown(f"Gemini Token: **{'Found' if gem_status['found'] else 'Missing'}**")
st.sidebar.markdown("Generation: **Local GPU inference**")
st.sidebar.markdown("Inference time: **~9–10 min (cold)**")

if not ootd_status["ready"]:
    st.sidebar.warning("OOTDiffusion venv or script not found — try-on will fail")

# Main Page
st.markdown('<h1 class="hero-title">StyleSense AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Computer Vision & Local GPU Try-On</p>', unsafe_allow_html=True)

up_col, cloth_col = st.columns(2)
with up_col:
    uploaded_file = st.file_uploader("Upload a full-body photo", type=["jpg", "jpeg", "png"], key="person_upload")
with cloth_col:
    cloth_file = st.file_uploader("Upload a garment image (for try-on)", type=["jpg", "jpeg", "png"], key="cloth_upload")

if uploaded_file is not None:
    if st.session_state.uploaded_bytes != uploaded_file.getvalue():
        st.session_state.uploaded_bytes = uploaded_file.getvalue()
        st.session_state.uploaded_img = Image.open(io.BytesIO(st.session_state.uploaded_bytes)).convert("RGB")
        for k in ["analysis_data", "outfit_ideas", "tryon_image", "llm_advice"]:
            st.session_state[k] = None

if cloth_file is not None:
    if st.session_state.cloth_bytes != cloth_file.getvalue():
        st.session_state.cloth_bytes = cloth_file.getvalue()
        st.session_state.cloth_img = Image.open(io.BytesIO(st.session_state.cloth_bytes)).convert("RGB")
        st.session_state.tryon_image = None

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>Person Photo</h3>", unsafe_allow_html=True)
        st.image(st.session_state.uploaded_img, width=None, use_container_width=True)
        if st.session_state.cloth_img:
            st.markdown("<h3>Garment</h3>", unsafe_allow_html=True)
            st.image(st.session_state.cloth_img, width=None, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        btn_label = "Analyze & Try On" if st.session_state.cloth_img else "Analyze Outfit"
        if st.button(btn_label, use_container_width=True, type="primary"):
            with st.spinner("Running Computer Vision Analysis..."):
                try:
                    # CV Analysis
                    analysis = analyze_outfit(st.session_state.uploaded_img)
                    st.session_state.analysis_data = analysis

                    # Recommendation Rules
                    ideas = generate_three_outfit_recommendations(analysis, user_gender, user_weather)
                    st.session_state.outfit_ideas = ideas

                    # OOTDiffusion try-on (only if cloth image provided)
                    if st.session_state.cloth_img:
                        with st.status("Running local GPU try-on (RTX 4050 cold-start: ~9–10 min)...", expanded=True) as ootd_status_box:
                            st.write("Loading OpenPose & human parsing models...")
                            st.write("Loading OOTDiffusion HD pipeline (~3 GB into VRAM)...")
                            st.write("Running diffusion inference (15 steps)...")
                            st.write("Please keep this tab open and do not refresh.")
                            try:
                                result = run_ootd_tryon(
                                    st.session_state.uploaded_img,
                                    st.session_state.cloth_img,
                                )
                                st.session_state.tryon_image = result
                                ootd_status_box.update(label="Try-on complete!", state="complete", expanded=False)
                            except RuntimeError as e:
                                ootd_status_box.update(label="Try-on failed", state="error", expanded=True)
                                st.error(f"Inference error: {e}")
                            except subprocess.TimeoutExpired:
                                ootd_status_box.update(label="Timed out after 20 min", state="error", expanded=True)
                                st.error("Inference timed out (>20 min). Close other GPU applications and retry.")

                    # Gemini Advice
                    with st.spinner("Consulting Gemini Stylist..."):
                        advice = generate_llm_fashion_advice(analysis, ideas, user_gender, user_weather)
                        st.session_state.llm_advice = advice

                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error during analysis pipeline: {e}")

    with col2:
        if st.session_state.analysis_data:
            data = st.session_state.analysis_data
            
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="margin-top:0;">Detected Style: <span class="accent-text">{data['style']}</span></h3>
                <p style="color:#a39bb8; font-size:1.1rem;">Confidence: {data['confidence']}%</p>
                <p style="color:#e2e8f0; font-style:italic;">{data['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            sc_col, oc_col = st.columns(2)
            with sc_col:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <h4 style="color:#a39bb8 !important;">Fashion Score</h4>
                    <div style="font-size:3.5rem; font-weight:800; color:#d4af37; line-height:1;">
                        {data['fashion_score']}<span style="font-size:1.5rem; color:#6853a0;">/100</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(data["fashion_score"])
                
            with oc_col:
                st.markdown(f"""
                <div class="glass-card card-equal-height" style="text-align:center;">
                    <h4 style="color:#a39bb8 !important;">Best Occasion</h4>
                    <p style="font-size:1.2rem; color:#f8fafc; margin-top:1rem; font-weight:500;">
                        {data['occasion']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3>Dominant Color Palette</h3>", unsafe_allow_html=True)
            for c in data["dominant_colors"]:
                st.markdown(f"""
                <div class="color-container">
                    <div class="color-circle" style="background-color:{c['hex']};"></div>
                    <div class="color-label">
                        <strong>{c['name']}</strong>
                        <span style="color:#6853a0;">({c['proportion']*100:.1f}%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.outfit_ideas:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<h2 class="accent-text" style="text-align:center;">AI Virtual Try-On Collection</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    outfit_cols = st.columns(3)

    for i in range(3):
        idea = st.session_state.outfit_ideas[i]
        with outfit_cols[i]:
            st.markdown(f'''
            <div class="glass-card card-equal-height">
                <h3 style="color:#d4af37; text-align:center; margin-top:0;">{idea['title']}</h3>
            ''', unsafe_allow_html=True)

            if i == 0 and isinstance(st.session_state.tryon_image, Image.Image):
                st.image(st.session_state.tryon_image, use_container_width=True)
                st.markdown('<p style="text-align:center; font-size:0.8rem; color:#a39bb8;">Local GPU try-on result</p>', unsafe_allow_html=True)
            else:
                placeholder_msg = "Upload a garment image to see the try-on." if i == 0 else "Outfit description only."
                st.markdown(f'''
                <div style="background: rgba(255,255,255,0.02); padding: 40px 20px; text-align: center; border-radius: 12px; border: 1px dashed rgba(212, 175, 55, 0.3); margin-bottom: 15px;">
                    <div style="color: #a39bb8; font-size: 0.9rem;">{placeholder_msg}</div>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown(f'''
                <div style="color:#e2e8f0; font-size: 0.9rem; margin-top:15px;">
                    <strong>Items:</strong> {idea['items']}<br><br>
                    <strong>Colors:</strong> {idea['colors']}<br><br>
                    <strong>Occasion:</strong> {idea['occasion']}<br><br>
                    <em style="color:#a39bb8;">"{idea['description']}"</em>
                </div>
            </div>
            ''', unsafe_allow_html=True)

if st.session_state.llm_advice:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<h2 class="accent-text" style="text-align:center;">Your Personal AI Stylist</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>Stylist Assessment</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#e2e8f0; font-size:1.1rem; line-height:1.6;'>{st.session_state.llm_advice}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>Ask Your Stylist</h3>", unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user"><strong>You:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bot"><strong style="color:#d4af37;">Stylist:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
                
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask a fashion question...")
            submit = st.form_submit_button("Ask Stylist")
            
            if submit and user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                response = answer_fashion_chat(user_input, st.session_state.analysis_data, st.session_state.outfit_ideas)
                st.session_state.chat_history.append({"role": "bot", "content": response})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
