# -*- coding: utf-8 -*-

"""
LLM Model Switcher for QStockAI.

使用 OpenAI 兼容接口支持多种 LLM 模型：
- MiniMax (推荐)
- Qwen (通义千问)
- OpenAI (GPT-4)
- Anthropic (Claude)

新版本使用 langchain-openai 的 ChatOpenAI 类，通过 openai_api_base
参数配置不同的 API 端点。
"""

from langchain_openai import ChatOpenAI
from typing import Optional, Literal

import src.config

# 支持的模型列表
SUPPORTED_PROVIDERS: list[Literal["minimax", "qwen", "openai", "anthropic"]] = [
    "minimax",
    "qwen",
    "openai",
    "anthropic",
]


def get_api_key_and_base(provider: str) -> tuple[str, str]:
    """
    根据 provider 获取对应的 API Key 和 base URL。

    Args:
        provider: 模型提供商

    Returns:
        tuple: (api_key, base_url)
    """
    if provider == "minimax":
        api_key = src.config.MINIMAX_API_KEY
        base_url = src.config.MINIMAX_API_BASE
        if not api_key:
            raise ValueError("MINIMAX_API_KEY 未设置，请在 .env 文件中配置")
        return api_key, base_url

    elif provider == "qwen":
        api_key = src.config.DASHSCOPE_API_KEY
        base_url = src.config.DASHSCOPE_API_BASE
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 未设置，请在 .env 文件中配置")
        return api_key, base_url

    elif provider == "openai":
        api_key = src.config.OPENAI_API_KEY
        base_url = "https://api.openai.com/v1"
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        return api_key, base_url

    elif provider == "anthropic":
        api_key = src.config.GOOGLE_API_KEY  # Note: 用户需要设置 ANTHROPIC_API_KEY
        base_url = "https://api.anthropic.com/v1"
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 未设置，请在 .env 文件中配置")
        return api_key, base_url

    else:
        raise ValueError(f"不支持的 provider: {provider}")


def get_model_name(provider: str) -> str:
    """获取对应 provider 的默认模型名称"""
    if provider == "minimax":
        return src.config.MINIMAX_MODEL
    elif provider == "qwen":
        return src.config.QWEN_MODEL
    elif provider == "openai":
        return "gpt-4o"
    elif provider == "anthropic":
        return "claude-3-5-sonnet-20241022"
    return "gpt-4o"


def init_llm(
    provider: str = None,
    model: str = None,
    temperature: float = 0.7,
    streaming: bool = False,
) -> Optional[ChatOpenAI]:
    """
    初始化并返回一个 LangChain ChatOpenAI 实例。

    支持通过 provider 或直接指定 model 两种方式调用：
        # 方式1: 指定 provider
        llm = init_llm("minimax")

        # 方式2: 直接指定模型 (会自动检测 provider)
        llm = init_llm(model="minimax/abab6.5s-chat")

    Args:
        provider: 模型提供商 ("minimax", "qwen", "openai", "anthropic")
        model: 可选，直接指定模型名称，格式如 "provider/model-name"
        temperature: 生成温度 (0-1)，越低越确定性
        streaming: 是否启用流式输出

    Returns:
        ChatOpenAI 实例，或 None (初始化失败时)
    """
    # 如果直接指定了 model，解析出 provider
    if model and not provider:
        if "/" in model:
            provider, actual_model = model.split("/", 1)
            model = actual_model
        else:
            # 尝试自动识别
            if model.startswith("abab") or model.startswith("minimax"):
                provider = "minimax"
            elif model.startswith("qwen"):
                provider = "qwen"
            elif model.startswith("gpt"):
                provider = "openai"
            elif model.startswith("claude"):
                provider = "anthropic"
            else:
                provider = src.config.DEFAULT_MODEL

    # 如果仍未指定，使用默认
    if not provider:
        provider = src.config.DEFAULT_MODEL

    # 检查 provider 是否支持
    if provider not in SUPPORTED_PROVIDERS:
        print(f"错误: 不支持的 provider '{provider}'")
        print(f"支持的 provider: {SUPPORTED_PROVIDERS}")
        return None

    try:
        api_key, base_url = get_api_key_and_base(provider)

        # 如果未指定 model，使用 provider 的默认模型
        if not model:
            model = get_model_name(provider)

        print(f"正在初始化 LLM: {provider}/{model}")
        print(f"API Base: {base_url}")

        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
        )

        print(f"成功初始化 {provider}/{model} 模型")
        return llm

    except ValueError as e:
        print(f"配置错误: {e}")
        return None
    except Exception as e:
        print(f"初始化 LLM 时发生错误: {e}")
        return None


def init_llm_with_fallback(
    primary_provider: str = "minimax",
    fallback_provider: str = "qwen",
    temperature: float = 0.7,
) -> Optional[ChatOpenAI]:
    """
    尝试主 provider，失败时自动切换到 fallback provider。

    Args:
        primary_provider: 主选 provider
        fallback_provider: 备用 provider
        temperature: 生成温度

    Returns:
        ChatOpenAI 实例，或 None (全部失败)
    """
    llm = init_llm(provider=primary_provider, temperature=temperature)
    if llm:
        return llm

    print(f"主 provider ({primary_provider}) 初始化失败，尝试备用 provider ({fallback_provider})...")
    return init_llm(provider=fallback_provider, temperature=temperature)


# --- 便捷函数 ---

def init_minimax(temperature: float = 0.7) -> Optional[ChatOpenAI]:
    """快速初始化 MiniMax 模型"""
    return init_llm(provider="minimax", temperature=temperature)


def init_qwen(temperature: float = 0.7) -> Optional[ChatOpenAI]:
    """快速初始化 Qwen (通义千问) 模型"""
    return init_llm(provider="qwen", temperature=temperature)


# --- 测试块 ---
if __name__ == "__main__":
    print("--- 测试 llm_switcher 模块 ---\n")

    # 测试 MiniMax
    print("1. 测试 MiniMax:")
    llm = init_minimax()
    if llm:
        try:
            response = llm.invoke("你好，请简短介绍一下自己")
            print(f"   响应: {response.content[:200]}...")
            print("   ✅ MiniMax 测试成功!\n")
        except Exception as e:
            print(f"   ❌ MiniMax 调用失败: {e}\n")

    # 测试 Qwen
    print("2. 测试 Qwen:")
    llm = init_qwen()
    if llm:
        try:
            response = llm.invoke("你好，请简短介绍一下自己")
            print(f"   响应: {response.content[:200]}...")
            print("   ✅ Qwen 测试成功!\n")
        except Exception as e:
            print(f"   ❌ Qwen 调用失败: {e}\n")

    # 测试 fallback
    print("3. 测试自动回退:")
    llm = init_llm_with_fallback()
    if llm:
        print(f"   ✅ 自动选择成功!\n")
    else:
        print("   ❌ 所有 provider 都失败了，请检查 API Key 配置\n")
