"""DeepSeek API client."""

import os
import time
from openai import APITimeoutError, APIConnectionError, InternalServerError, OpenAI, RateLimitError


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
    resp = client.chat.completions.create(model="deepseek-chat", messages=messages, timeout=30)
    return resp.choices[0].message.content


def chat_with_tools(messages, tools):
    client = get_client()
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(model="deepseek-chat", messages=messages, tools=tools, timeout=30)
            return (resp.choices[0].message, resp.usage)
        except (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError) as e:
            if attempt == 2:
                raise e
            time.sleep(2 ** attempt)
