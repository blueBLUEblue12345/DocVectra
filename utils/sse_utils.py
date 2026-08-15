"""SSE (Server-Sent Events) 会话队列管理

用于流式接口：节点处理过程把增量内容 push 到会话队列，
前端通过 /stream/{session_id} 轮询消费，实现实时流式返回。
"""
import asyncio
import json
import queue
import threading
from enum import Enum


class SSEEvent(str, Enum):
    """SSE 事件类型"""
    START = "start"
    DELTA = "delta"
    FINAL = "final"
    ERROR = "error"


_queues: dict = {}
_lock = threading.Lock()


def _get_queue(session_id: str) -> "queue.Queue":
    with _lock:
        if session_id not in _queues:
            _queues[session_id] = queue.Queue()
        return _queues[session_id]


def create_sse_queue(session_id: str) -> None:
    """为会话创建结果队列（幂等）"""
    _get_queue(session_id)


def push_to_session(session_id: str, event, data) -> None:
    """向会话队列推送一个事件"""
    try:
        event_name = event.value if isinstance(event, SSEEvent) else str(event)
        _get_queue(session_id).put({"event": event_name, "data": data})
    except KeyError:
        pass


async def sse_generator(session_id: str, request):
    """SSE 生成器：从队列取事件，格式化后 yield 给前端"""
    q = _get_queue(session_id)
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                item = await asyncio.to_thread(q.get, True, 1.0)
            except queue.Empty:
                continue
            yield f"event: {item['event']}\ndata: {json.dumps(item['data'], ensure_ascii=False)}\n\n"
    finally:
        with _lock:
            if session_id in _queues:
                del _queues[session_id]
