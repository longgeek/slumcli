import time

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Span:
    type: str
    name: str
    started_at: datetime
    duration_ms: int | None = None
    input: str = ""
    output: str = ""
    metadata: dict = field(default_factory=dict)
    

@dataclass
class Trace:
    trace_id: str
    user_input: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "running"
    spans: list = field(default_factory=list)
    
    
def _truncate(text: str, limit: int = 500):
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def start_trace(user_input: str) -> Trace:
    return Trace(
        trace_id=str(uuid4()),
        user_input=user_input,
        started_at=datetime.now()
    )
    
def finish_trace(trace: Trace, status: str = "completed") -> None:
    trace.ended_at = datetime.now()
    trace.status = status
    
def add_span(trace, span_type, name, input_data, **metadata) -> Span:
    truncated = _truncate(input_data, 500)
    span = Span(
        type=span_type,
        name=name,
        started_at=datetime.now(),
        input=truncated,
        metadata=metadata
    )
    trace.spans.append(span)
    return span

def end_span(span, output_data=""):
    span.duration_ms = int((datetime.now() - span.started_at).total_seconds() * 1000)
    span.output = _truncate(output_data, 500)
    

def print_trace(trace: Trace) -> None:
    print(f"\n========== Trace Start {trace.trace_id} ==========")
    print(f"Status: {trace.status}")
    print(f"Started at: {trace.started_at}")
    print(f"Ended at: {trace.ended_at}")
    print(f"Total duration: {(trace.ended_at - trace.started_at).total_seconds()}s")
    print(f"Spans: {len(trace.spans)}")
    
    for index, span in enumerate(trace.spans):
        print(f"[{index + 1}] {span.type}: {span.name} | {span.duration_ms}ms")
        print(f".   input: {span.input}")
        print(f".   output: {span.output}")
        print(f".   metadata: {span.metadata}")
    print(f"========== Trace End {trace.trace_id} ==========")

    
if __name__ == "__main__":
    # s = Span(
    #     type="tool",
    #     name="read_file",
    #     started_at=datetime.now(),
    #     input='{"path": "main.py"}'
    # )
    # b = start_trace("read the file main.py")
    # print(s)
    # print(b)
    # 
    # print(_truncate("hello", 10))
    # print(_truncate("hello" * 600, 10))
    # 
    # print("----")
    trace = start_trace("读 main.py")
    span = add_span(trace, "tool", "read_file", '{"path": "main.py"}')
    time.sleep(1)
    end_span(span, "内容: print('hello')")
    finish_trace(trace, "completed")
    print_trace(trace)