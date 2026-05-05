import os, time
import streamlit as st
from components.chat import render_chat_view
from components.dashboard import render_dashboard
from components.config_panel import render_config_panel
from components.style import inject_custom_css, get_theme
from ui.utils.api import APIClient
from ui.utils.ws import WebSocketClient, process_incoming_messages, get_retry_status

st.set_page_config(page_title="俺寻思 AI 工厂", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# ==== Session State 初始化 ====
api_host = os.environ.get("IRECKON_API_HOST", "localhost")
api_port = os.environ.get("IRECKON_API_PORT", "8000")
api_base = f"http://{api_host}:{api_port}"
ws_base = f"ws://{api_host}:{api_port}"

if "api_client" not in st.session_state: st.session_state.api_client = APIClient(api_base)
if "ws_client" not in st.session_state: st.session_state.ws_client = WebSocketClient(ws_base)
if "current_task_id" not in st.session_state: st.session_state.current_task_id = None
if "messages" not in st.session_state: st.session_state.messages = []
if "theme_name" not in st.session_state: st.session_state.theme_name = "catgirl"
if "view_mode" not in st.session_state: st.session_state.view_mode = "styled"
if "show_new_task" not in st.session_state: st.session_state.show_new_task = False
if "dark_mode" not in st.session_state: st.session_state.dark_mode = True
if "show_config" not in st.session_state: st.session_state.show_config = False
if "task_progress" not in st.session_state: st.session_state.task_progress = 0
if "task_status" not in st.session_state: st.session_state.task_status = ""
if "log_messages" not in st.session_state: st.session_state.log_messages = []
if "last_ws_rerun" not in st.session_state: st.session_state.last_ws_rerun = 0
if "last_reconnect_attempt" not in st.session_state: st.session_state.last_reconnect_attempt = 0
if "ai_statuses" not in st.session_state: st.session_state.ai_statuses = {}
if "self_improve_status" not in st.session_state: st.session_state.self_improve_status = None
if "show_instance_form" not in st.session_state: st.session_state.show_instance_form = False
if "editing_instance" not in st.session_state: st.session_state.editing_instance = None

# ==== 注入CSS ====
inject_custom_css()

# ==== 顶部工具栏 ====
with st.container():
    c = st.columns([1.5, 3, 1, 1, 1, 1, 1, 1, 1])
    with c[0]: st.markdown("### 🤖 俺寻思")
    with c[1]:
        tasks = st.session_state.api_client.get_tasks()
        running = [t for t in tasks if t["status"] in ("planning","executing","reviewing","revising")]
        if running: st.caption(f"🔄 {len(running)} 运行中  |  共 {len(tasks)} 任务")
        else: st.caption(f"💤 空闲  |  共 {len(tasks)} 任务")
    with c[2]:
        d = st.session_state.dark_mode
        if st.button("🌙" if d else "☀️", key="dt"): st.session_state.dark_mode = not d; st.rerun()
    with c[3]:
        if st.button("➕ 新任务"): st.session_state.show_new_task = True; st.rerun()
    with c[4]:
        if st.session_state.current_task_id and st.button("⏹ 停止"):
            st.session_state.api_client._request("POST", f"/api/tasks/{st.session_state.current_task_id}/cancel")
    with c[5]:
        if st.button("🔄 恢复"):
            p = [t for t in tasks if t["status"] in ("pending","paused","planning","executing","reviewing","revising")]
            if p:
                for t in p: st.session_state.api_client._request("POST", f"/api/tasks/{t[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)]}/resume")
                st.success(f"恢复 {len(p)} 个"); st.rerun()
            else: st.info("没有待恢复任务")
    with c[6]:
        import requests as rq
        if st.button("🔍 诊断"):
            with st.spinner("检查中..."):
                try:
                    resp = rq.get(f"http://{api_host}:{api_port}/api/diagnostics", timeout=10)
                    d = resp.json()
                    if d.get("status") == "ok":
                        for name, status in d.get("checks", {}).items():
                            e = "✅" if status == "ok" else "❌"
                            st.caption(f"{e} {name}: {status}")
                    else: st.error("诊断失败")
                except Exception as e: st.error(f"诊断失败: {e}")
    with c[7]:
        themes = st.session_state.api_client._request("GET", "/api/themes") or {}
        tn = list(themes.keys()) if themes else ["catgirl","programmer","raw"]
        cur = st.session_state.get("theme_name", "catgirl")
        idx = tn.index(cur) if cur in tn else 0
        new_t = st.selectbox("主题", tn, index=idx, key="theme_sel", label_visibility="collapsed")
        if new_t != cur: st.session_state.theme_name = new_t; st.session_state.api_client.update_config({"ui.theme": new_t}); st.rerun()
        if st.button("⚙️ 配置"): st.session_state.show_config = not st.session_state.show_config; st.rerun()
    with c[8]:
        if st.button("🔄 刷新"): st.rerun()

st.divider()

# ==== 新任务弹窗 ====
if st.session_state.show_new_task:
    with st.form("new_task_form"):
        req = st.text_area("描述需求", height=100)
        if st.form_submit_button("启动") and req:
            resp = st.session_state.api_client.create_task(req)
            if resp:
                st.session_state.current_task_id = resp["task_id"]
                st.session_state.ws_client.connect(resp["task_id"])
                st.session_state.show_new_task = False; st.rerun()
            else: st.error("创建失败")

# ==== 配置页面（全屏）====
if st.session_state.get("show_config", False):
    st.title("⚙️ 配置中心")
    render_config_panel()
    if st.button("✕ 关闭配置", use_container_width=True):
        st.session_state.show_config = False; st.rerun()
else:
    # ==== 主界面 ====
    # 任务选择
    all_tasks = st.session_state.api_client.get_tasks()
    if all_tasks:
        opts = {t["task_id"]: f"{t["user_request"][:30]}... ({t["status"]})" for t in all_tasks}
        sel = st.selectbox("选择任务", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
        if sel and sel != st.session_state.current_task_id:
            st.session_state.current_task_id = sel
            api = st.session_state.api_client
            l1 = api.get_messages(sel, layer="L1")
            l2 = api.get_messages(sel, layer="L2")
            l3 = api.get_messages(sel, layer="L3")
            msgs = l1 + l2 + l3
            msgs.sort(key=lambda x: x.get("timestamp", ""))
            st.session_state.messages = msgs
            st.session_state.ws_client.connect(sel)
    else:
        st.info("还没有任务，点 ➕ 新任务 开始")

    # 待恢复任务 - 显眼的单个恢复按钮
    pending = [t for t in all_tasks if t["status"] in ("pending","paused","planning","executing","reviewing","revising")]
    if pending:
        st.markdown(f"### 📋 {len(pending)} 个未完成任务")
        for t in pending[:5]:
            cc, rc = st.columns([5,1])
            with cc:
                st.caption(f"{t[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)][:10]}: {t["user_request"][:35]}")
            with rc:
                if st.button("▶️ 恢复", key=f"r_{t[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)]}", help="恢复此任务"):
                    st.session_state.api_client._request("POST", f"/api/tasks/{t[chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100)]}/resume")
                    st.success("已请求恢复"); st.rerun()
        if len(pending) > 5:
            st.caption(f"...还有 {len(pending)-5} 个")
        st.divider()
    # 主内容区
    tid = st.session_state.current_task_id
    tab1, tab2 = st.tabs(["💬 群聊广场", "📊 仪表盘"])
    with tab1:
        if tid:
            render_chat_view(tid, st.session_state.messages, get_theme(st.session_state.theme_name),
                           st.session_state.view_mode, st.session_state.api_client)
        else:
            st.info("选择或创建一个任务")
    with tab2:
        if tid: render_dashboard(tid)
        else: st.info("选择或创建一个任务")

    # WebSocket消息处理
    if process_incoming_messages():
        now = time.time()
        if now - st.session_state.last_ws_rerun >= 0.5:
            st.session_state.last_ws_rerun = now; st.rerun()

    if tid:
        ws = st.session_state.ws_client
        if not ws.is_connected() and time.time() - st.session_state.last_reconnect_attempt > 5:
            ws.connect(tid)
            st.session_state.last_reconnect_attempt = time.time()