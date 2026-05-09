import streamlit as st
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False
    psutil = None
from datetime import datetime

def render_dashboard(task_id: str):
    api = st.session_state.get("api_client")
    
    # Header
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <span style="font-size: 24px;">📊</span>
        <h2 style="margin: 0;">任务仪表盘</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress Section
    progress = st.session_state.get("task_progress", 0)
    status = st.session_state.get("task_status", "idle")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(min(progress, 1.0), text=f"进度: {int(progress*100)}%")
    with col2:
        status_colors = {
            "planning": "🟡",
            "executing": "🔵",
            "reviewing": "🟣",
            "completed": "🟢",
            "error": "🔴",
        }
        status_label = status_colors.get(status, "⚪")
        st.markdown(f"<div class='badge'>{status_label} {status.upper()}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # System Metrics - Modern Cards
    st.markdown("### 🖥️ 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    cpu = psutil.cpu_percent() if _HAS_PSUTIL else 0
    mem = psutil.virtual_memory().percent if _HAS_PSUTIL else 0
    disk = psutil.disk_usage('/').percent if _HAS_PSUTIL else 0
    
    with col1:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 16px;">
            <div style="font-size: 24px; font-weight: 700;">{cpu:.0f}%</div>
            <div style="color: var(--text-secondary); font-size: 12px;">CPU</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 16px;">
            <div style="font-size: 24px; font-weight: 700;">{mem:.0f}%</div>
            <div style="color: var(--text-secondary); font-size: 12px;">内存</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 16px;">
            <div style="font-size: 24px; font-weight: 700;">{disk:.0f}%</div>
            <div style="color: var(--text-secondary); font-size: 12px;">磁盘</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        active = st.session_state.get("active_task_count", 0)
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 16px;">
            <div style="font-size: 24px; font-weight: 700;">{active}</div>
            <div style="color: var(--text-secondary); font-size: 12px;">活跃任务</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Real-time Logs - Modern Style
    st.markdown("### 📝 实时日志")
    
    with st.container(height=300):
        logs = st.session_state.get("log_messages", [])
        if logs:
            for log in reversed(logs[-20:]):
                level = log.get('level', 'INFO')
                msg = log.get('message', '')
                ts = log.get('timestamp', '')
                
                if isinstance(ts, datetime):
                    ts = ts.strftime("%H:%M:%S")
                
                level_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}.get(level, "📝")
                
                st.markdown(f"""
                <div style="padding: 8px 12px; margin: 4px 0; border-left: 3px solid var(--border); background: var(--bg-card); border-radius: 8px; font-family: monospace; font-size: 12px;">
                    <span style="color: var(--text-secondary);">[{ts}]</span>
                    <span style="margin: 0 8px;">{level_emoji}</span>
                    <span>{msg}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; color: var(--text-secondary); padding: 40px;">
                <span style="font-size: 32px;">📭</span>
                <p>暂无日志...</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Diagnostics
    st.markdown("---")
    st.markdown("### 🔍 系统诊断")
    if st.button("运行诊断", use_container_width=True, key="diag_btn"):
        if api:
            result = api._request("GET", "/api/diagnostics")
            if result:
                checks = result.get("checks", {})
                for name, status in checks.items():
                    st.markdown(f"- **{name}**: {status}")
                stats = result.get("stats", {})
                if stats:
                    st.markdown("#### 统计信息")
                    for name, val in stats.items():
                        st.markdown(f"- **{name}**: {val}")
            else:
                st.error("诊断请求失败")
        else:
            st.error("API 客户端未初始化")
    
    # 系统信息
    st.markdown("---")
    with st.expander("🔧 系统信息", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("API状态", "🟢 在线" if api else "🔴 离线")
        with col2:
            st.metric("版本", "3.0")