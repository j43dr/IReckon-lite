"""
IReckon Config Panel - Clean, single-purpose configuration UI
"""
import streamlit as st


def _safe_idx(options: list, value, default: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return default


def render_config_panel():
    api = st.session_state.get("api_client")
    if api is None:
        st.warning("API 客户端未初始化")
        return

    config = api.get_config() or {}
    if not config:
        st.warning("无法加载配置")
        return

    # ---- AI Instances ----
    st.subheader("AI 实例管理")
    instances = api.get_ai_instances() or []

    for inst in instances:
        if "instance_id" in inst and "id" not in inst:
            inst["id"] = inst["instance_id"]

    if instances:
        rows = []
        for i in instances:
            cost = float(i.get("cost_per_1k_tokens", 0))
            rows.append({
                "ID": i.get("id", "")[:14],
                "名称": i.get("name", ""),
                "模型": i.get("model", "")[:24],
                "价格/1k": f"${cost:.6f}",
                "标签": ",".join(i.get("tags", [])[:2]),
                "状态": "启用" if i.get("enabled", True) else "禁用",
            })
        if rows:
            try:
                import pandas as pd
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            except ImportError:
                for row in rows:
                    st.text(" | ".join(f"{k}: {v}" for k, v in row.items()))

    # Instance actions
    instance_ids = [i["id"] for i in instances if i.get("id")]
    selected = st.selectbox("选择实例", [""] + instance_ids, key="inst_select")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("添加实例", width="stretch"):
            pass
        if st.button("编辑实例", width="stretch"):
            pass
    with col_b:
        if st.button("删除实例", width="stretch"):
            pass
        if st.button("测试连接", width="stretch"):
            pass
    with col_c:
        if st.form_submit_button("保存", width="stretch"):
            st.success("已保存")
    with col_d:
        if st.button("保存重试设置", width="stretch"):
            pass
        if st.button("保存任务设置", width="stretch"):
            pass
        if st.button("保存服务器设置 (需重启)", width="stretch"):
            st.info("服务器设置保存需重启后生效")