import streamlit as st
from pathlib import Path
import json

def load_theme(theme_name: str) -> dict:
    theme_path = Path("config/themes") / f"{theme_name}.json"
    if theme_path.exists():
        with open(theme_path, "r", encoding="utf-8") as f:
            return json.load(f)
    fallback_path = Path(__file__).parent.parent.parent / "config" / "themes" / f"{theme_name}.json"
    if fallback_path.exists():
        with open(fallback_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "默认", "role_mapping": {
        "scheduler": {"name": "调度官", "avatar": "📋"},
        "executor": {"name": "工程师", "avatar": "💻"},
        "reviewer_efficiency": {"name": "架构师", "avatar": "🏗️"},
        "reviewer_correctness": {"name": "测试员", "avatar": "🔬"},
        "user": {"name": "你", "avatar": "👤"},
    }}

def get_theme(theme_name: str) -> dict:
    return load_theme(theme_name)

def inject_custom_css():
    dark_mode = st.session_state.get("dark_mode", True)
    
    if dark_mode:
        # ========== 深色主题 - Cyberpunk Style ==========
        bg_main = "#0a0a0f"
        bg_sidebar = "#12121a"
        bg_card = "#16161f"
        bg_input = "#1e1e28"
        text_color = "#e4e4e7"
        text_secondary = "#71717a"
        text_muted = "#52525b"
        border_color = "#27272a"
        border_light = "#3f3f46"
        
        # Accent colors - Cyberpunk neon
        primary = "#06b6d4"      # Cyan
        secondary = "#f472c6"     # Pink
        accent = "#a855f7"        # Purple
        success = "#22c55e"
        warning = "#eab308"
        error = "#ef4444"
        
        # Gradient accents
        gradient_1 = "linear-gradient(135deg, #06b6d4 0%, #a855f7 100%)"
        gradient_2 = "linear-gradient(135deg, #f472c6 0%, #06b6d4 100%)"
        
        # Chat colors
        msg_bg_user = "#1e3a5f"
        msg_bg_ai = "#0f172a"
        msg_user_border = "#22d3ee"
        msg_ai_border = "#a855f7"
        
    else:
        # ========== 浅色主题 - Modern Clean ==========
        bg_main = "#f8fafc"
        bg_sidebar = "#ffffff"
        bg_card = "#ffffff"
        bg_input = "#f1f5f9"
        text_color = "#1e293b"
        text_secondary = "#64748b"
        text_muted = "#94a3b8"
        border_color = "#e2e8f0"
        border_light = "#f1f5f9"
        
        primary = "#0ea5e9"      # Sky blue - 更亮
        secondary = "#ec4899"   # Pink - 更亮
        accent = "#8b5cf6"       # Purple - 更亮
        success = "#10b981"
        warning = "#f59e0b"
        error = "#ef4444"
        
        gradient_1 = "linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%)"
        gradient_2 = "linear-gradient(135deg, #ec4899 0%, #0ea5e9 100%)"
        
        msg_bg_user = "#e0f2fe"
        msg_bg_ai = "#f5f3ff"
        msg_user_border = "#0ea5e9"
        msg_ai_border = "#8b5cf6"

    st.markdown(f"""
    <style>
    /* ===== 基础重置 ===== */
    .stApp {{
        background-color: {bg_main} !important;
        color: {text_color} !important;
    }}
    
    /* ===== 标题样式 ===== */
    h1, h2, h3 {{
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }}
    h1 {{ font-size: 2.25rem !important; }}
    h2 {{ font-size: 1.75rem !important; }}
    h3 {{ font-size: 1.25rem !important; }}
    
    /* ===== 链接 ===== */
    a {{
        color: {primary} !important;
        text-decoration: none !important;
        transition: color 0.2s !important;
    }}
    a:hover {{
        color: {secondary} !important;
    }}
    
    /* ===== 侧边栏 ===== */
    section[data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {border_color} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    
    /* ===== 卡片 ===== */
    .card {{
        background-color: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
    }}
    .card:hover {{
        border-color: {primary}33 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    }}
    
    /* ===== 聊天气泡 ===== */
    .stChatMessageContainer {{
        gap: 12px !important;
    }}
    div[data-testid="stChatMessage"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 20px !important;
        padding: 16px 20px !important;
        max-width: 85% !important;
    }}
    div[data-testid="stChatMessage"]:has(.avatar-user) {{
        background: {msg_bg_user} !important;
        border-color: {msg_user_border} !important;
        margin-left: auto !important;
        border-bottom-right-radius: 4px !important;
    }}
    div[data-testid="stChatMessage"]:has(.avatar-ai) {{
        background: {msg_bg_ai} !important;
        border-color: {msg_ai_border} !important;
        margin-right: auto !important;
        border-bottom-left-radius: 4px !important;
    }}
    
    /* ===== 输入框 ===== */
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="input"] input {{
        background-color: {bg_input} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
        padding: 14px 16px !important;
        font-size: 15px !important;
        transition: all 0.2s !important;
    }}
    div[data-baseweb="textarea"] textarea:focus,
    div[data-baseweb="input"] input:focus {{
        border-color: {primary} !important;
        box-shadow: 0 0 0 3px {primary}1a !important;
        outline: none !important;
    }}
    
    /* ===== 按钮 ===== */
    .stButton > button {{
        background: {gradient_1} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.025em !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.15) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(0,0,0,0.25) !important;
    }}
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid {border_color} !important;
        box-shadow: none !important;
        color: {text_secondary} !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: {error} !important;
        color: {error} !important;
    }}
    
    /* ===== 选择框 ===== */
    div[data-baseweb="select"] > div {{
        background-color: {bg_input} !important;
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }}
    
    /* ===== 标签页 ===== */
    button[data-baseweb="tab"] {{
        color: {text_secondary} !important;
        font-weight: 500 !important;
        padding: 12px 20px !important;
        border-radius: 12px 12px 0 0 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {primary} !important;
        background: {bg_card} !important;
        border-bottom: 2px solid {primary} !important;
    }}
    
    /* ===== 进度条 ===== */
    .stProgress > div > div {{
        background: {gradient_1} !important;
        border-radius: 9999px !important;
    }}
    
    /* ===== 警告/成功/信息框 ===== */
    .stAlert {{
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 16px !important;
    }}
    
    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {bg_main};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {border_color};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {text_secondary};
    }}
    
    /* ===== 响应式布局 ===== */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 1rem !important;
            max-width: 100% !important;
        }}
        section[data-testid="stSidebar"] {{
            min-width: 100% !important;
            max-width: 100% !important;
        }}
        h1 {{ font-size: 1.5rem !important; }}
        h2 {{ font-size: 1.25rem !important; }}
        div[data-testid="stChatMessage"] {{
            padding: 12px 16px !important;
            max-width: 95% !important;
        }}
    }}
    
    /* ===== 动画 ===== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateX(-10px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    .animate-fade-in {{
        animation: fadeIn 0.3s ease-out;
    }}
    .animate-pulse {{
        animation: pulse 2s infinite;
    }}
    .animate-slide-in {{
        animation: slideIn 0.3s ease-out;
    }}
    
    /* ===== 徽章 ===== */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 500;
        border-radius: 9999px;
        background: {primary}20;
        color: {primary};
    }}
    .badge-success {{
        background: {success}20;
        color: {success};
    }}
    .badge-warning {{
        background: {warning}20;
        color: {warning};
    }}
    .badge-error {{
        background: {error}20;
        color: {error};
    }}
    
    /* ===== 分割线 ===== */
    hr {{
        border: none;
        height: 1px;
        background: {border_color};
        margin: 24px 0;
    }}
    
    /* ===== 标签 ===== */
    .stChip {{
        border-radius: 9999px !important;
    }}
    
    /* ===== 展开器 ===== */
    div[data-testid="stExpander"] {{
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}
    </style>
    
    <script>
    // 给聊天消息添加动画类
    function addChatAnimations() {{
        const messages = document.querySelectorAll('[data-testid="stChatMessage"]');
        messages.forEach((msg, i) => {{
            msg.style.animationDelay = (i * 0.1) + 's';
        }});
    }}
    
    // 初始化
    document.addEventListener('DOMContentLoaded', addChatAnimations);
    // 定期检查新消息
    setInterval(addChatAnimations, 1000);
    </script>
    """, unsafe_allow_html=True)

def get_ai_status_html(status: str) -> str:
    status_map = {
        "thinking": ("🧠 思考中", "badge-warning"),
        "output": ("💬 输出中", "badge"),
        "idle": ("✓ 空闲", "badge-success"),
        "error": ("✗ 错误", "badge-error"),
        "retrying": ("🔄 重试中", "badge"),
    }
    label, cls = status_map.get(status, ("", "badge"))
    if label:
        return f'<span class="badge {cls}">{label}</span>'
    return ""