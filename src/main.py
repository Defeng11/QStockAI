# -*- coding: utf-8 -*-

"""
Main entry point for the Streamlit application.
"""

import streamlit as st

def main():
    st.title("量子选股 (LiangZiXuanGu) AI Agent")

    st.header("免责声明")
    st.warning(
        "本项目及其生成的所有内容仅供学习和研究目的，不构成任何投资建议。"
        "股市有风险，投资需谨慎。基于本项目信息做出的任何投资决策，风险自负。"
    )

    st.sidebar.header("设置")
    # UI elements will be added here

    st.header("分析结果")
    # Results will be displayed here

if __name__ == "__main__":
    main()
