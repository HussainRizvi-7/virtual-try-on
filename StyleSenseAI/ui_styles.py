# ui_styles.py

css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800&display=swap');

    html, body, [class*="css"] { 
        font-family: 'Outfit', sans-serif; 
    }

    .stApp {
        background: linear-gradient(135deg, #0f0f11 0%, #1a1a24 100%);
        color: #f8fafc;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #4a3b72; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #6853a0; }

    /* Hero */
    .hero-title {
        font-weight: 800 !important;
        font-size: 5rem !important;
        letter-spacing: -2px !important;
        background: linear-gradient(to right, #d4af37, #f3e5ab, #d4af37);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite;
        margin-bottom: 0 !important;
        text-align: center;
    }
    @keyframes shine { to { background-position: 200% center; } }

    .hero-subtitle {
        font-size: 1.5rem;
        color: #a39bb8;
        margin-bottom: 3rem;
        font-weight: 300;
        letter-spacing: 3px;
        text-align: center;
        text-transform: uppercase;
    }

    h1, h2, h3, h4 { font-weight: 600 !important; color: #f3e5ab !important; }

    .accent-text { color: #d4af37; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }

    /* Glassmorphism cards */
    .glass-card {
        background: rgba(30, 25, 40, 0.5);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(212, 175, 55, 0.15);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 40px -10px rgba(0,0,0,0.7);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px -10px rgba(212, 175, 55, 0.2);
        border: 1px solid rgba(212, 175, 55, 0.4);
    }
    
    .card-equal-height {
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Colour swatches */
    .color-circle {
        display: inline-block; width: 40px; height: 40px;
        border-radius: 50%; margin-right: 15px; margin-bottom: 15px;
        border: 2px solid rgba(212, 175, 55, 0.3);
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .color-container { display: flex; align-items: center; margin-bottom: 12px; }
    .color-label { font-size: 1rem; color: #e2e8f0; margin-left: 12px; }

    /* Progress bars */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #6853a0 0%, #d4af37 100%);
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1e1a2b 0%, #0f0f11 100%);
        color: #d4af37;
        border: 1px solid rgba(212, 175, 55, 0.4);
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6853a0 0%, #4a3b72 100%);
        border: 1px solid transparent;
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(104, 83, 160, 0.5);
        color: white;
    }

    /* Chat bubbles */
    .chat-user {
        background: rgba(212, 175, 55, 0.1);
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 16px 16px 0 16px;
        padding: 15px 20px; margin-bottom: 15px; text-align: right;
        color: #e2e8f0;
    }
    .chat-bot {
        background: rgba(104, 83, 160, 0.15);
        border: 1px solid rgba(104, 83, 160, 0.3);
        border-radius: 16px 16px 16px 0;
        padding: 15px 20px; margin-bottom: 15px;
        color: #e2e8f0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b0b0e;
        border-right: 1px solid rgba(212, 175, 55, 0.1);
    }
</style>
"""
