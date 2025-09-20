# This is the main entry point for the Streamlit multi-page application.
# Streamlit will automatically discover pages in the 'pages' subdirectory.

import streamlit as st

st.set_page_config(page_title="LiangZiXuanGu - 量子选股", layout="wide")

st.title("量子选股 (LiangZiXuanGu) AI Agent")
st.markdown("一个基于LangGraph多代理工作流的A股智能分析投研工具。")

st.info("请在左侧导航栏选择功能页面。")
