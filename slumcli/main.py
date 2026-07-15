"""slumcli entry point."""

import sys

from dotenv import load_dotenv

from slumcli.client import chat_with_tools
from slumcli.tools import TOOLS, run_tool
from slumcli.context import trim_messages
from slumcli.prompts import SYSTEM_PROMPT
from slumcli.security import confirm_tool, audit_log
from slumcli.tracing import start_trace, finish_trace, add_span, end_span, print_trace


def vlog(verbose: bool, msg: str) -> None:
    if verbose:
        print(msg, file=sys.stderr)


def parse_args(argv: list[str]):
    return "-v" in argv

def main() -> None:
    """Run the minimal agent: read input → call API → print reply."""
    load_dotenv()
    verbose = parse_args(sys.argv[1:])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            user_input = input("You: ")
        except (KeyboardInterrupt, EOFError) as e:
            print(f"bye")
            break

        if user_input in ["exit", "/q"]:
            break
        elif user_input == "/n":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            continue
        elif user_input == "/h":
            print("Usage: /q to exit, /n to new task, /h to show help")
            continue
        
        trace = start_trace(user_input)
        messages.append({"role": "user", "content": user_input})
        trim_messages(messages)
        try:
            reply = run_turn(messages, verbose, trace)
        except Exception as e:
            print(f"Error: {e}")
            continue
        finish_trace(trace)
        print_trace(trace)

def run_turn(messages, verbose, trace):
    span = add_span(trace, "llm", "llm", f"{len(messages)} messages")
    reply, usage = chat_with_tools(messages, TOOLS)
    span.metadata["total_tokens"] = usage.total_tokens
    end_span(span, reply.content)
    if reply.tool_calls:
        names = [tc.function.name for tc in reply.tool_calls]
        vlog(verbose, f"[verbose] tool_calls: {names}")
    else:
        vlog(verbose, "[verbose] direct reply (no tools)")

    turn = 0
    while reply.tool_calls and turn < 10:
        turn += 1
        messages.append(reply.model_dump())
        for tool_call in reply.tool_calls:
            name = tool_call.function.name
            args = tool_call.function.arguments
            vlog(verbose, f"[verbose] turn {turn}: {name}({args})")
            span = add_span(trace, "tool_call", name, args)
            if confirm_tool(name, args):
                result = run_tool(name, args)
                if "blocked" in result.lower():
                    outcome = "blocked"
                elif result.startswith("Error:"):
                    outcome = "error"
                else:
                    outcome = "executed"
            else:
                result = "Tool execution cancelled by user"
                outcome = "denied"
            audit_log(name, args, outcome)
            preview = result[:200] + ("..." if len(result) > 200 else "")
            vlog(verbose, f"[verbose] result: {preview}")
            messages.append({"role": "tool", "content": result, "tool_call_id": tool_call.id})
            end_span(span, result)
        span = add_span(trace, "llm", "llm", f"{len(messages)} messages")
        reply, usage = chat_with_tools(messages, TOOLS)
        span.metadata["total_tokens"] = usage.total_tokens
        end_span(span, reply.content)
        if reply.tool_calls:
            names = [tc.function.name for tc in reply.tool_calls]
            vlog(verbose, f"[verbose] tool_calls: {names}")
            if turn == 10:
                print("⚠️ 任务未在 10 轮内完成,已停止。")
                return

    vlog(verbose, f"[verbose] done, {turn} tool turn(s)")
    messages.append({"role": "assistant", "content": reply.content})
    return reply.content


if __name__ == "__main__":
    main()
