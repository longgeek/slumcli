"""DeepSeek API client."""

import os
from openai import OpenAI


def get_client() -> OpenAI:
    """Create and return an OpenAI-compatible client for DeepSeek.

    TODO: 从环境变量读取 DEEPSEEK_API_KEY，设置 base_url 为 DeepSeek 地址。
    """
    return OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")


def chat(messages: list[dict[str, str]]) -> str:
    """Send messages to DeepSeek and return the assistant reply.

    Args:
        messages: OpenAI-format message list, e.g.
            [{"role": "user", "content": "hello"}]

    Returns:
        The assistant's reply text.

    TODO:
        1. 用 get_client() 拿到 client
        2. 调 client.chat.completions.create，model="deepseek-chat"
        3. 从 response.choices[0].message.content 取出回复字符串并返回
    """
    client = get_client()
    resp = client.chat.completions.create(model="deepseek-chat", messages=messages)
    return resp.choices[0].message.content


def chat_with_tools(messages, tools):
    client = get_client()
    resp = client.chat.completions.create(model="deepseek-chat", messages=messages, tools=tools)
    return resp.choices[0].message