# -*- coding: utf-8 -*- 

"""
Module for switching between different Large Language Models (LLMs).
"""

from langchain_community.chat_models import ChatTongyi
# from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI

import src.config

SUPPORTED_MODELS = ["qwen-max", "qwen-turbo", "qwen-plus"]

def init_llm(model_name: str = "qwen-max"):
    """
    Initializes and returns a LangChain chat model instance based on the model name.

    Args:
        model_name (str): The name of the model to initialize.

    Returns:
        A LangChain chat model instance, or None if the model is not supported or API key is missing.
    """
    print(f"正在初始化LLM: {model_name}")

    if model_name in ["qwen-max", "qwen-turbo", "qwen-plus"]:
        if not src.config.DASHSCOPE_API_KEY:
            print(f"错误: DASHSCOPE_API_KEY 未设置。请在 .env 文件中提供。")
            return None
        try:
            llm = ChatTongyi(
                model_name=model_name,
                dashscope_api_key=src.config.DASHSCOPE_API_KEY
            )
            print(f"成功初始化 {model_name} 模型。")
            return llm
        except Exception as e:
            print(f"初始化 ChatTongyi 模型时出错: {e}")
            return None

    # Add other models here in the future
    # elif model_name == "gpt-4":
    #     if not config.OPENAI_API_KEY:
    #         print("错误: OPENAI_API_KEY 未设置。")
    #         return None
    #     return ChatOpenAI(model_name=model_name, openai_api_key=config.OPENAI_API_KEY)

    else:
        print(f"错误: 不支持的模型 '{model_name}'。支持的模型: {SUPPORTED_MODELS}")
        return None


# --- Test Block ---
if __name__ == '__main__':
    print("--- 测试 llm_switcher 模块 ---")
    print("该测试将尝试初始化默认的 'qwen-max' 模型。")
    print("\n要使测试成功，请确保：")
    print("1. 项目根目录下有一个名为 .env 的文件。")
    print("2. .env 文件中包含了您的有效 DASHSCOPE_API_KEY，格式如下：")
    print("   DASHSCOPE_API_KEY=\"sk-xxxxxxxxxxxxxxxxxxxxxx\"")
    print("-" * 20)

    llm_instance = init_llm()

    if llm_instance:
        print("\n模型实例创建成功，正在尝试调用...")
        try:
            # Simple invocation test
            response = llm_instance.invoke("你好")
            print("\n模型调用成功！返回内容：")
            print(response.content)
            print("\n测试通过！")
        except Exception as e:
            print(f"\n模型调用失败: {e}")
            print("请检查您的API Key是否有效、账户是否正常。")
    else:
        print("\n模型实例创建失败。请根据上面的提示检查您的配置。")