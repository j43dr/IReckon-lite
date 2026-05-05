import streamlit as st
from datetime import datetime

def get_ai_name(api_client, agent_id):
    if "ai_names" not in st.session_state:
        try:
            instances = api_client.get_ai_instances()
            st.session_state.ai_names = {i["id"]: i["name"] for i in instances} if instances else {}
        except:
            st.session_state.ai_names = {}
    return st.session_state.ai_names.get(agent_id, agent_id[:8] if agent_id else "?")

def render_chat_view(task_id, messages, theme, view_mode, api_client=None):
    tab_l1, tab_l2, tab_l3 = st.tabs(["🏛️ 公共广场", "🤖 AI会议室 (L2)", "🔒 私聊 (L3)"])
    with tab_l1:
        ai_statuses = st.session_state.get("ai_statuses", {})
        if ai_statuses:
            status_cols = st.columns(min(len(ai_statuses), 4))
            for i, (agent_id, status) in enumerate(list(ai_statuses.items())[:4]):
                with status_cols[i % 4]:
                    role_info = theme.get("role_mapping", {}).get(agent_id, {})
                    name = role_info.get("name", agent_id[:6])
                    avatar = role_info.get("avatar", "🤖")
                    emoji_map = {"thinking": "🧠", "output": "💬", "idle": "✅", "error": "❌", "retrying": "🔄"}
                    st.caption(f"{avatar} {name} {emoji_map.get(status, '')}")
        
        _render_message_list([m for m in messages if m.get("layer") == "L1"], theme, view_mode, api_client)
        _render_input_box(task_id, api_client, layer="L1")
    with tab_l2:
        st.caption("🤖 AI 团队会议 - 各角色之间的协作对话")
        _render_message_list([m for m in messages if m.get("layer") == "L2"], theme, view_mode, api_client)
    with tab_l3:
        _render_message_list([m for m in messages if m.get("layer") == "L3"], theme, view_mode, api_client)
        st.caption("🔒 AI 之间的私聊，仅供查看")

def _render_message_list(msgs, theme, view_mode, api_client):
    if not msgs:
        st.info("还没有消息，创建一个任务开始吧 ✨")
        return
    for msg in msgs:
        render_message(msg, theme, view_mode, api_client)

def render_message(msg, theme, view_mode, api_client):
    role = msg.get("sender_role", "system")
    content = msg.get("content", "")
    sender_id = msg.get("sender_id", "")
    timestamp = msg.get("timestamp", "")
    
    role_mapping = theme.get("role_mapping", {})
    role_info = role_mapping.get(role, {})
    display_name = role_info.get("name", role.capitalize())
    avatar = role_info.get("avatar", "🤖" if role != "user" else "👤")
    
    if sender_id and role != "user":
        ai_name = get_ai_name(api_client, sender_id)
        display_name = f"{display_name} ({ai_name})"
    
    if role == "user":
        display_name = "你"
        avatar = "👤"
    
    time_str = ""
    if timestamp:
        try:
            t = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = t.strftime("%H:%M:%S")
        except:
            time_str = timestamp[-8:] if len(timestamp) > 8 else ""
    
    with st.chat_message(name=display_name, avatar=avatar):
        if time_str:
            st.caption(f"🕐 {time_str}")
        
        if view_mode == "raw":
            st.text(content if content else "(空)")
        else:
            # 风格化显示
            if role == "user":
                st.markdown(f'<div style="color: #4CAF50; font-weight: 500;">{content}</div>', 
                           unsafe_allow_html=True)
            elif role == "scheduler":
                st.info(content)
            elif role == "reviewer":
                if "通过" in content or "pass" in content.lower():
                    st.success(content)
                elif "需修改" in content or "fail" in content.lower():
                    st.warning(content)
                else:
                    st.markdown(f'<div style="border-left: 3px solid #ff9800; padding-left: 10px;">{content}</div>',
                               unsafe_allow_html=True)
            elif role == "executor":
                st.markdown(f'<div style="font-family: monospace; background: rgba(0,0,0,0.05); padding: 8px; border-radius: 8px; white-space: pre-wrap;">{content[:500]}</div>',
                           unsafe_allow_html=True)
                if len(content) > 500:
                    with st.expander("查看完整代码"):
                        st.code(content, language="python")
            else:
                st.markdown(content)

def _render_input_box(task_id, api_client, layer="L1"):
    with st.form(key=f"chat_input_{layer}", clear_on_submit=True):
        cols = st.columns([6, 1])
        with cols[0]:
            prompt = st.text_area("输入消息", placeholder="输入消息...", 
                                 label_visibility="collapsed", height=40,
                                 key=f"input_{layer}")
        with cols[1]:
            sent = st.form_submit_button("发送", use_container_width=True)
        if sent and prompt and task_id:
            api_client.send_message(task_id, prompt, layer=layer)
            st.rerun()
