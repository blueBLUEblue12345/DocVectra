"""Redis 任务状态管理模块

维护每个 TaskID 的全局状态、已完成节点、运行中节点和最终结果。
数据存于 Redis，服务重启后状态可恢复。
"""
import json
import os
import threading
from typing import Any, Optional

import redis
from dotenv import load_dotenv

load_dotenv()

TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

REDIS_KEY_PREFIX = "docvectra:task:"
REDIS_KEY_STATUS = "status"
REDIS_KEY_DONE = "done_list"
REDIS_KEY_RUNNING = "running_list"
REDIS_KEY_RESULT = "result"

_redis_client: Optional[redis.Redis] = None
_lock = threading.Lock()


def _get_redis_client() -> redis.Redis:
    global _redis_client
    with _lock:
        if _redis_client is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
        return _redis_client


def _task_key(task_id: str, field: str) -> str:
    return f"{REDIS_KEY_PREFIX}{task_id}:{field}"


def update_task_status(task_id: str, status: str, is_stream: bool = None) -> None:
    r = _get_redis_client()
    r.set(_task_key(task_id, REDIS_KEY_STATUS), status)


def get_task_status(task_id: str) -> str:
    r = _get_redis_client()
    status = r.get(_task_key(task_id, REDIS_KEY_STATUS))
    return status if status else TASK_STATUS_PENDING


def add_done_task(task_id: str, node_name: str) -> None:
    r = _get_redis_client()
    key = _task_key(task_id, REDIS_KEY_DONE)
    if r.sismember(key, node_name):
        return
    r.sadd(key, node_name)


def get_done_task_list(task_id: str) -> list:
    r = _get_redis_client()
    return list(r.smembers(_task_key(task_id, REDIS_KEY_DONE)))


def add_running_task(task_id: str, node_name: str) -> None:
    r = _get_redis_client()
    key = _task_key(task_id, REDIS_KEY_RUNNING)
    if r.sismember(key, node_name):
        return
    r.sadd(key, node_name)


def get_running_task_list(task_id: str) -> list:
    r = _get_redis_client()
    return list(r.smembers(_task_key(task_id, REDIS_KEY_RUNNING)))


def set_task_result(task_id: str, key: str, value: Any) -> None:
    r = _get_redis_client()
    result_key = _task_key(task_id, REDIS_KEY_RESULT)
    result_json = r.get(result_key)
    result_dict = json.loads(result_json) if result_json else {}
    result_dict[key] = value
    r.set(result_key, json.dumps(result_dict, ensure_ascii=False))


def get_task_result(task_id: str, key: str, default=None) -> Any:
    r = _get_redis_client()
    result_json = r.get(_task_key(task_id, REDIS_KEY_RESULT))
    if not result_json:
        return default
    result_dict = json.loads(result_json)
    return result_dict.get(key, default)
