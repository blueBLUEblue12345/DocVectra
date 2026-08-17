import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from processor.query_processor.main_graph import KBQueryWorkflow
from tools.logger import logger
from utils.mongo_history_utils import clear_history, get_recent_messages
from utils.sse_utils import SSEEvent, create_sse_queue, push_to_session, sse_generator
from utils.task_utils import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PROCESSING,
    get_task_result,
    update_task_status,
)

# 1. 创建应用
app = FastAPI(
    title="掌柜智库-查询API",
    description="此文档是掌柜智库查询流程的API接口说明"
)

# 2. 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)

# 定义接口接收的数据结构
class QueryRequest(BaseModel):
    """查询请求数据结构"""
    query: str = Field(..., description="查询内容")  # ...必须填写
    session_id: str = Field(None, description="会话ID")
    is_stream: bool = Field(False, description="是否流式返回")



@app.post("/query")
async def query(background_tasks: BackgroundTasks, request: QueryRequest):
    """
    1 解析参数
    2 更新任务状态
    3 调用处理流程图
    4 返回结果
    :param background_tasks:
    :param request:
    :return:
    """
    user_query = request.query
    session_id = request.session_id if request.session_id else str(uuid.uuid4())

    # 处理是不是流式返回结果
    is_stream = request.is_stream
    if is_stream:
        # 创建一个字典 存储对一个session_id : queue 结果队列
        create_sse_queue(session_id)
    # 更新任务状态
    # 当前会话id作为key! 整体装填处于运行中！
    update_task_status(session_id, TASK_STATUS_PROCESSING,is_stream)

    logger.info(f"开始处理流程... 是否流式: {is_stream}, 其他参数: {user_query}, session_id: {session_id}")

    if is_stream:
        # 如果是流式，则返回一个流式响应，过程不断地推送
        # 运行执行图对象方法
        background_tasks.add_task(run_query_graph, session_id,user_query,is_stream)
        # 返回结果
        logger.info("开始处理结果....")
        return {
            "message":"结果正在处理中...",
            "session_id":session_id
        }
    else:
        # 同步运行
        run_query_graph(session_id, user_query, is_stream)
        answer = get_task_result(session_id,"answer","")
        return {
            "message":"处理完成！",
            "session_id":session_id,
            "answer":answer,
            "done_list":[]
        }

# 定义查询接口
def run_query_graph(session_id: str, user_query: str, is_stream: bool = True):
    logger.info(f"开始流程图处理... {session_id} {user_query} {is_stream}")

    init_state = {
        "original_query": user_query,
        "session_id": session_id,
        "is_stream": is_stream
    }

    try:
        workflow = KBQueryWorkflow()
        for event in workflow.run(init_state, stream=True):
            logger.info(f"工作流事件: {list(event.keys())}")
        update_task_status(session_id, TASK_STATUS_COMPLETED, is_stream)
    except Exception as e:
        logger.error(f"流程执行异常: {e}", exc_info=True)
        update_task_status(session_id, TASK_STATUS_FAILED, is_stream)
        if is_stream:
            push_to_session(session_id, SSEEvent.ERROR, {"error": str(e)})

@app.get("/stream/{session_id}")
async def stream(session_id: str, request: Request):
    logger.info("调用流式/stream...")
    """
    sse 实时返回结果
    """
    return StreamingResponse(
        sse_generator(session_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    清空指定会话的历史记录
    """
    count = clear_history(session_id)
    return {"message": "历史会话已清空", "deleted_count": count}

@app.get("/history/{session_id}")
async def history(session_id: str, limit: int = 50):
    """
    查询当前会话历史记录
    """
    try:
        records = get_recent_messages(session_id, limit=limit)
        items = []
        for r in records:
            items.append({
                "_id": str(r.get("_id")) if r.get("_id") is not None else "",
                "session_id": r.get("session_id", ""),
                "role": r.get("role", ""),
                "text": r.get("text", ""),
                "rewritten_query": r.get("rewritten_query", ""),
                "item_names": r.get("item_names", []),
                "ts": r.get("ts")
            })
        return {"session_id": session_id, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"history error: {e}")


# 证明服务器启动即可
@app.get("/health")
async def health():
    """
    检查服务是否正常
    """
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)