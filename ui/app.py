"""
IReckon 3.0 - 全新UI设计
移动优先、现代化设计、流畅交互
"""
import streamlit as st
import os
import time
from ui.components.config_panel import render_config_panel
from ui.components.dashboard import render_dashboard
from ui.utils.api import APIClient

st.set_page_config(
    page_title="IReckon 3.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# ===== API配置 =====
API_HOST = os.environ.get("IRECKON_API_HOST", "localhost")
API_PORT = os.environ.get("IRECKON_API_PORT", "8000")
API_BASE = f"http://{API_HOST}:{API_PORT}"

# ===== 会话状态初始化 =====
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.messages = []
    st.session_state.current_task_id = None
    st.session_state.task_status = "idle"
    st.session_state.task_progress = 0.0
    st.session_state.dark_mode = True
    st.session_state.theme = "dark"
    st.session_state.show_status = True
    st.session_state.infinite_retry = False
    st.session_state.max_retries = 10
    st.session_state.api_timeout = 30
    
    # 尝试从API加载配置，失败则使用默认值
    try:
        import requests
        r = requests.get(f"{API_BASE}/api/config", timeout=3)
        if r.status_code == 200:
            cfg = r.json()
            st.session_state.theme = cfg.get("theme", "dark")
            st.session_state.dark_mode = cfg.get("dark_mode", True)
            st.session_state.show_status = cfg.get("show_status", True)
            st.session_state.max_retries = cfg.get("ai_pool", {}).get("retry", {}).get("max_retries", 10)
    except Exception:
        pass
    st.session_state.last_update = time.time()

# 初始化API客户端
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient(API_BASE)

# 获取当前主题配置
dark_mode = st.session_state.get("dark_mode", True)

# ===== 动态样式 =====
if dark_mode:
    st.markdown("""
    <style>
    /* 夜间模式 - 深色 */
    :root {
        --bg-primary: #0f0f14;
        --bg-secondary: #18181f;
        --bg-card: #1e1e28;
        --bg-input: #252530;
        --text-primary: #e8e8ec;
        --text-secondary: #8888a0;
        --accent-primary: #3b82f6;
        --accent-secondary: #06b6d4;
        --accent-gradient: linear-gradient(135deg, #3b82f6, #06b6d4);
        --success: #22c55e;
        --warning: #eab308;
        --error: #ef4444;
        --border: #2a2a3a;
    }
    .stApp {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    /* 白天模式 - 白色带蓝色渐变 */
    :root {
        --bg-primary: #f0f4f8;
        --bg-secondary: #ffffff;
        --bg-card: #ffffff;
        --bg-input: #f8fafc;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --accent-primary: #2563eb;
        --accent-secondary: #0ea5e9;
        --accent-gradient: linear-gradient(135deg, #2563eb, #0ea5e9);
        --success: #16a34a;
        --warning: #ca8a04;
        --error: #dc2626;
        --border: #e2e8f0;
    }
    .stApp {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ===== 全局自定义CSS =====
st.markdown("""
<style>
/* 按钮样式 */
div.stButton > button {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.2s;
}
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
div.stButton > button[kind="secondary"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* 输入框样式 */
div.stTextInput > div > div > input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px;
}
div.stTextInput > div > div > input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 卡片样式 */
div[data-testid="stExpander"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
}

/* 复选框 */
div[data-testid="stCheckbox"] > label {
    color: var(--text-primary);
}

/* 开关 */
div[data-testid="stToggle"] > label {
    color: var(--text-primary);
}

/* 选择框 */
div[data-testid="stSelectbox"] > div > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* 数字输入框 */
div[data-testid="stNumberInput"] input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* 文本域 */
div[data-testid="stTextArea"] > div > div > textarea {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* 进度条 */
div[data-testid="stProgress"] > div > div {
    background: var(--accent-gradient) !important;
}

/* 标签页 */
div[data-testid="stTabs"] button {
    color: var(--text-secondary) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent-primary) !important;
    border-bottom: 2px solid var(--accent-primary) !important;
}

/* 滚动条 */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}
::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}

/* 顶部标题栏 */
.title-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    margin: -1rem -1rem 1rem -1rem;
}
.title-logo {
    font-size: 24px;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.title-status {
    display: flex;
    align-items: center;
    gap: 12px;
}

/* 卡片容器 */
.config-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.config-card h3 {
    color: var(--text-primary);
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}

/* 消息气泡 */
.chat-bubble {
    padding: 12px 16px;
    border-radius: 16px;
    margin-bottom: 8px;
    max-width: 80%;
}
.chat-bubble-user {
    background: var(--accent-gradient);
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.chat-bubble-assistant {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
}

/* 发送按钮 */
.send-button {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
}
.send-button:hover {
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# ===== 标题栏 =====
col_title_left, col_title_right = st.columns([3, 1])

with col_title_left:
    st.markdown("""
    <div class="title-logo">🤖 IReckon 3.0</div>
    """, unsafe_allow_html=True)

with col_title_right:
    col_theme, col_status = st.columns(2)
    with col_theme:
        # 明暗切换按钮 - 按钮文字显示当前模式，点击后切换
        current_dark = st.session_state.get("dark_mode", True)
        theme_icon = "🌙" if current_dark else "☀️"
        theme_label = "切换白天" if current_dark else "切换夜间"
        if st.button(f"{theme_icon} {theme_label}", use_container_width=True, key="theme_toggle_btn"):
            new_dark_mode = not current_dark
            st.session_state.dark_mode = new_dark_mode
            try:
                import requests
                requests.post(f"{API_BASE}/api/config/update", 
                    json={"updates": {"dark_mode": new_dark_mode}}, timeout=3)
            except Exception:
                pass
            st.rerun()
    with col_status:
        # 状态显示开关
        show_status_val = st.session_state.get("show_status", True)
        show_status_new = st.checkbox("显示状态", value=show_status_val, key="status_toggle_main")
        if show_status_new != show_status_val:
            st.session_state.show_status = show_status_new
            try:
                import requests
                requests.post(f"{API_BASE}/api/config/update", 
                    json={"updates": {"show_status": show_status_new}}, timeout=3)
            except Exception:
                pass
            st.rerun()

# ===== 主内容区 =====
tab_chat, tab_config, tab_diag = st.tabs(["💬 对话", "⚙️ 配置", "🔧 诊断"])

# ===== 对话标签页 =====
with tab_chat:
    # 显示任务进度
    show_status = st.session_state.get("show_status", True)
    if show_status:
        task_status = st.session_state.get("task_status", "idle")
        task_progress = st.session_state.get("task_progress", 0.0)
        
        status_icons = {
            "idle": "🟢",
            "planning": "🟡",
            "executing": "🔵",
            "reviewing": "🟣",
            "completed": "✅",
            "error": "🔴"
        }
        status_text = {
            "idle": "空闲",
            "planning": "思考中",
            "executing": "执行中",
            "reviewing": "审核中",
            "completed": "已完成",
            "error": "出错"
        }
        
        st.markdown(f"""
        <div class="config-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>{status_icons.get(task_status, '⚪')} {status_text.get(task_status, '未知')}</span>
                <span style="color: var(--text-secondary);">{int(task_progress * 100)}%</span>
            </div>
            <div style="margin-top: 8px; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden;">
                <div style="height: 100%; width: {task_progress * 100}%; background: var(--accent-gradient); border-radius: 3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 聊天消息区域
    chat_container = st.container()
    with chat_container:
        messages = st.session_state.get("messages", [])
        for msg in messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            is_user = role == "user"
            bubble_class = "chat-bubble-user" if is_user else "chat-bubble-assistant"
            emoji = "👤" if is_user else "🤖"
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <div style="font-size: 11px; opacity: 0.7; margin-bottom: 4px;">{emoji}</div>
                {content}
            </div>
            """, unsafe_allow_html=True)
    
    # 欢迎提示
    if not messages:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
            <div style="font-size: 56px; margin-bottom: 16px;">🤖</div>
            <h2 style="color: var(--text-primary);">欢迎使用 IReckon 3.0</h2>
            <p>在下方输入框中描述你想要完成的任务</p>
            <p style="font-size: 13px; opacity: 0.7; margin-top: 12px;">
                例：帮我写一个Python爬虫脚本<br>
                例：帮我优化这段代码的性能
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 输入区域 - 修复空label问题
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        user_input = st.text_input(
            "输入任务描述", 
            placeholder="在这里描述你想要完成的任务...",
            key="chat_input",
            label_visibility="visible"
        )
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        send_clicked = st.button("🚀 发送", use_container_width=True, key="send_btn")
    
    # 清除按钮
    with st.container():
        clear_clicked = st.button("🗑️ 清除对话", use_container_width=True, key="clear_btn")

    # 处理发送
    if send_clicked and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            import requests
            r = requests.post(
                f"{API_BASE}/api/tasks",
                json={"user_request": user_input},
                timeout=30
            )
            
            if r.status_code in [200, 201]:
                result = r.json()
                task_id = result.get("task_id", "")
                st.session_state.current_task_id = task_id
                st.session_state.task_status = "executing"
                st.session_state.task_progress = 0.1
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"✅ 任务已创建: {task_id}\n正在处理你的请求..."
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"❌ 创建失败: {r.status_code}"
                })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"❌ 错误: {str(e)}"
            })
        
        st.rerun()
    
    # 处理清除
    if clear_clicked:
        st.session_state.messages = []
        st.session_state.current_task_id = None
        st.session_state.task_status = "idle"
        st.session_state.task_progress = 0.0
        st.rerun()
    
    # 模拟进度更新 (使用时间戳控制频率，避免阻塞UI)
    current_task = st.session_state.get("current_task_id")
    task_status = st.session_state.get("task_status", "idle")
    task_progress = st.session_state.get("task_progress", 0.0)
    
    if current_task and task_status == "executing":
        now = time.time()
        last_update = st.session_state.get("_last_progress_update", 0)
        if now - last_update >= 0.3:
            new_progress = min(task_progress + 0.1, 1.0)
            st.session_state.task_progress = new_progress
            st.session_state._last_progress_update = now
            
            if new_progress >= 1.0:
                st.session_state.task_status = "completed"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "✅ 任务完成！"
                })
            st.rerun()

# ===== 配置标签页 =====
with tab_config:
    render_config_panel()

# ===== 诊断标签页 =====
with tab_diag:
    render_dashboard(st.session_state.get("current_task_id", ""))