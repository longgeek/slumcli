"""DeepSeek API client."""

import os
import time
from openai import APITimeoutError, APIConnectionError, InternalServerError, OpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function


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


def _consume_stream(resp):
    """把流式 chunk 收成 (message, usage),边收文本边打印。"""
    full = ""                 # 攒完整文本
    tool_calls = {}           # index -> {id, name, arguments}
    usage = None

    for chunk in resp:
        if chunk.usage is not None:      # 带 include_usage 时,最后一个 chunk 才有 usage
            usage = chunk.usage
        if not chunk.choices:            # 那个只带 usage 的 chunk,choices 是空的
            continue

        delta = chunk.choices[0].delta
        if delta.content:                # 文本:边收边打印 + 累加
            print(delta.content, end="", flush=True)
            full += delta.content
        if delta.tool_calls:             # 工具碎片:按 index 重组(和探针一样)
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls:
                    tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                if tc.id:
                    tool_calls[idx]["id"] = tc.id
                if tc.function.name:
                    tool_calls[idx]["name"] = tc.function.name
                if tc.function.arguments:
                    tool_calls[idx]["arguments"] += tc.function.arguments

    if full:                             # 有文本才补个换行,收尾
        print()

    # 把重组结果拼回 SDK 的消息对象,run_turn 就完全不用改
    calls = [
        ChatCompletionMessageToolCall(
            id=c["id"],
            type="function",
            function=Function(name=c["name"], arguments=c["arguments"]),
        )
        for c in tool_calls.values()
    ]
    message = ChatCompletionMessage(role="assistant", content=full, tool_calls=calls or None)
    return (message, usage)


def chat_with_tools(messages, tools):
    client = get_client()
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=messages, tools=tools, timeout=30,
                stream=True, stream_options={"include_usage": True},
            )
            return _consume_stream(resp)
        except (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError) as e:
            if attempt == 2:
                raise e
            time.sleep(2 ** attempt)
