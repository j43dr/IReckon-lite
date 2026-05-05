import streamlit as st
import pandas as pd

def render_config_panel():
    api = st.session_state.api_client
    
    # ============ AI 实例管理 ============
    st.markdown("### 🤖 AI 能力池管理")
    if st.button("🔄 刷新实例列表"):
        st.rerun()

    instances = api.get_ai_instances()
    if not instances:
        st.info("暂无 AI 实例，请添加")
        instances = []

    if instances:
        df = pd.DataFrame(instances)
        cols = [c for c in ["id", "name", "model", "endpoint", "enabled", "tags", "cost_per_1k_tokens"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True)

    st.markdown("#### 操作")
    instance_ids = [i['id'] for i in instances]
    selected_for_action = st.selectbox("选择实例", [""] + instance_ids, key="action_select")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ 添加"):
            st.session_state.editing_instance = None
            st.session_state.show_instance_form = True
    with col2:
        if st.button("✏️ 编辑"):
            if selected_for_action:
                inst = next((i for i in instances if i['id'] == selected_for_action), None)
                if inst:
                    st.session_state.editing_instance = inst
                    st.session_state.show_instance_form = True
            else:
                st.warning("请先选择一个实例")
    with col3:
        if st.button("🗑️ 删除"):
            if selected_for_action:
                api.delete_ai_instance(selected_for_action)
                st.success("已删除")
                st.rerun()
            else:
                st.warning("请先选择一个实例")
    with col4:
        if st.button("🔌 测试连接"):
            if selected_for_action:
                result = api.test_ai_instance(selected_for_action)
                if result:
                    if result.get("status") == "reachable":
                        st.success(f"✅ 连接成功 (HTTP {result['http_status']})")
                    else:
                        st.error(f"❌ 无法连接: {result.get('error')}")
                else:
                    st.error("测试请求失败")
            else:
                st.warning("请先选择一个实例")

    if st.session_state.get("show_instance_form"):
        with st.form("ai_instance_form"):
            edit = st.session_state.get("editing_instance")
            is_edit = edit is not None
            st.subheader("编辑实例" if is_edit else "添加实例")
            inst_id = st.text_input("ID", value=edit["id"] if is_edit else "", disabled=is_edit)
            name = st.text_input("名称", value=edit["name"] if is_edit else "")
            endpoint = st.text_input("API 端点", value=edit["endpoint"] if is_edit else "http://localhost:11434")
            model = st.text_input("模型名", value=edit["model"] if is_edit else "qwen2.5:7b")
            api_key = st.text_input("API Key", type="password", value=edit.get("api_key","") if is_edit else "")
            tags_str = st.text_input("标签 (逗号分隔)", value=",".join(edit["tags"]) if is_edit else "")
            cost_per_m = st.number_input("每百万token成本 ($)", value=float(edit.get("cost_per_1k_tokens", 0.0)) * 1000 if is_edit else 0.0, min_value=0.0, step=0.001, format="%.6f")
            max_ctx = st.number_input("最大上下文长度", value=int(edit.get("max_context", 4096)) if is_edit else 4096)
            enabled = st.checkbox("启用", value=edit.get("enabled", True) if is_edit else True)
            temperature = st.slider("默认温度", 0.0, 1.0, value=float(edit.get("parameters", {}).get("temperature", 0.3)) if is_edit else 0.3)
            max_tokens = st.number_input("默认最大生成token", value=int(edit.get("parameters", {}).get("max_tokens", 4096)) if is_edit else 4096)

            submitted = st.form_submit_button("保存")
            if submitted:
                cost_per_1k = cost_per_m / 1000.0
                data = {
                    "id": inst_id, "name": name, "endpoint": endpoint, "model": model,
                    "api_key": api_key if api_key else (edit.get("api_key","") if is_edit else ""),
                    "parameters": {"temperature": temperature, "max_tokens": max_tokens},
                    "tags": [t.strip() for t in tags_str.split(",") if t.strip()],
                    "cost_per_1k_tokens": cost_per_1k, "max_context": max_ctx, "enabled": enabled,
                }
                resp = api.update_ai_instance(inst_id, data) if is_edit else api.create_ai_instance(data)
                if resp:
                    st.success("保存成功")
                    st.session_state.show_instance_form = False
                    st.rerun()
                else:
                    st.error("保存失败")
        if st.button("取消"):
            st.session_state.show_instance_form = False
            st.rerun()

    st.markdown("---")

    # ============ 系统配置 ============
    st.markdown("### ⚙️ 系统配置")
    
    config = api._request("GET", "/api/config")
    if not config:
        st.warning("无法加载配置")
        return
    
    # 用tab分组
    tab_names = ["🤖 AI重试", "📋 任务默认", "🌐 服务器", "🎨 界面"]
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        ai_retry = config.get("ai_pool", {}).get("retry", {})
        col1, col2 = st.columns(2)
        with col1:
            new_max_retries = st.number_input("最大重试次数 (-1=无限)", 
                value=int(ai_retry.get("max_retries", 10)), min_value=-1, step=1)
            new_notify_after = st.number_input("通知阈值 (超过此次数发通知)",
                value=int(ai_retry.get("notify_after", 10)), min_value=1, step=1)
            new_base_delay = st.number_input("初始重试延迟(秒)",
                value=float(ai_retry.get("base_delay", 1.0)), min_value=0.1, step=0.1, format="%.1f")
        with col2:
            new_max_delay = st.number_input("最大重试延迟(秒)",
                value=float(ai_retry.get("max_delay", 30.0)), min_value=1.0, step=1.0, format="%.1f")
            new_exp_base = st.number_input("延迟指数基数",
                value=float(ai_retry.get("exponential_base", 2.0)), min_value=1.0, step=0.1, format="%.1f")
            new_infinite = st.checkbox("无限重试", value=ai_retry.get("infinite_retry", False))
        
        new_concurrency = st.number_input("最大并发调用数",
            value=int(config.get("ai_pool", {}).get("concurrency", {}).get("max_concurrent_calls", 5)), min_value=1, step=1)
        
        if st.button("保存 AI 重试设置", use_container_width=True):
            updates = {
                "ai_pool.retry.max_retries": new_max_retries,
                "ai_pool.retry.notify_after": new_notify_after,
                "ai_pool.retry.base_delay": new_base_delay,
                "ai_pool.retry.max_delay": new_max_delay,
                "ai_pool.retry.exponential_base": new_exp_base,
                "ai_pool.retry.infinite_retry": new_infinite,
                "ai_pool.concurrency.max_concurrent_calls": new_concurrency,
            }
            if api.update_config(updates):
                st.success("✅ 已保存")
                st.rerun()
            else:
                st.error("保存失败")

    with tabs[1]:
        td = config.get("task_defaults", {})
        col1, col2 = st.columns(2)
        with col1:
            new_timeout = st.number_input("任务超时(秒)", value=int(td.get("max_task_duration_seconds", 3600)), min_value=60, step=60)
            new_budget = st.number_input("预算上限($)", value=float(td.get("budget_limit_usd", 1.0)), min_value=0.0, step=0.1, format="%.2f")
            new_temp = st.slider("默认温度", 0.0, 1.0, value=float(td.get("default_temperature", 0.3)))
            new_max_review = st.number_input("最大评审轮次", value=int(td.get("max_review_rounds", 5)), min_value=1, step=1)
        with col2:
            new_pass_threshold = st.slider("通过阈值", 0.0, 1.0, value=float(td.get("pass_threshold", 0.8)))
            new_agent_timeout = st.number_input("AI调用超时(秒)", value=int(td.get("agent_call_timeout", 120)), min_value=10, step=10)
            new_max_tools = st.number_input("每模块最大工具调用", value=int(td.get("max_tool_calls_per_module", 10)), min_value=1, step=1)
        
        if st.button("保存任务默认设置", use_container_width=True):
            updates = {
                "task_defaults.max_task_duration_seconds": new_timeout,
                "task_defaults.budget_limit_usd": new_budget,
                "task_defaults.default_temperature": new_temp,
                "task_defaults.max_review_rounds": new_max_review,
                "task_defaults.pass_threshold": new_pass_threshold,
                "task_defaults.agent_call_timeout": new_agent_timeout,
                "task_defaults.max_tool_calls_per_module": new_max_tools,
            }
            if api.update_config(updates):
                st.success("✅ 已保存")
                st.rerun()

    with tabs[2]:
        sv = config.get("server", {})
        col1, col2 = st.columns(2)
        with col1:
            new_host = st.text_input("监听地址", value=sv.get("host", "0.0.0.0"))
            new_port = st.number_input("端口", value=int(sv.get("port", 8000)), min_value=1, max_value=65535)
        with col2:
            new_log_level = st.selectbox("日志级别", ["DEBUG", "INFO", "WARNING", "ERROR"], 
                                         index=["DEBUG","INFO","WARNING","ERROR"].index(sv.get("log_level", "INFO")))
        
        if st.button("保存服务器设置 (需重启)", use_container_width=True):
            updates = {"server.host": new_host, "server.port": new_port, "server.log_level": new_log_level}
            if api.update_config(updates):
                st.success("✅ 已保存，重启后生效")

    with tabs[3]:
        themes = api._request("GET", "/api/themes") or {}
        theme_names = list(themes.keys()) if themes else ["catgirl", "programmer", "raw"]
        default_theme = st.selectbox("默认主题", options=theme_names, 
            index=theme_names.index(st.session_state.get("theme_name", "catgirl")) if st.session_state.get("theme_name") in theme_names else 0)
        if default_theme != st.session_state.get("theme_name"):
            st.session_state.theme_name = default_theme
            api.update_config({"ui.theme": default_theme})

        default_view = st.selectbox("默认视图", ["styled", "raw"], 
            index=0 if st.session_state.get("view_mode")=="styled" else 1)
        if default_view != st.session_state.get("view_mode"):
            st.session_state.view_mode = default_view
            api.update_config({"ui.default_view": default_view})

    st.markdown("---")
    
    # ============ 学习与自我改进 ============
    st.markdown("### 🧬 学习与自我改进")
    lr = config.get("learning", {})
    su = config.get("self_update", {})
    col1, col2 = st.columns(2)
    with col1:
        new_idle_minutes = st.number_input("空闲触发(分钟)", value=int(lr.get("idle_trigger_minutes", 30)), min_value=1, step=5)
        new_self_enabled = st.checkbox("启用自我改进", value=su.get("enabled", True))
    with col2:
        new_high_end_model = st.text_input("高端模型ID", value=lr.get("high_end_model_id", ""))
    
    if st.button("保存学习设置", use_container_width=True):
        updates = {
            "learning.idle_trigger_minutes": new_idle_minutes,
            "learning.high_end_model_id": new_high_end_model,
            "self_update.enabled": new_self_enabled,
        }
        if api.update_config(updates):
            st.success("✅ 已保存")
            st.rerun()
