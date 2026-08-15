"""
DocVectra 知识库系统 - 统一入口

将导入服务和查询服务合并到一个 FastAPI 应用中
"""
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import import_service, query_service
from backend.health_check import check_all_services
from tools.logger import logger

# 创建主应用
app = FastAPI(
    title="DocVectra 知识库系统",
    description="企业级智能知识库系统，支持文档导入和智能问答"
)

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动时检查依赖服务"""
    if not check_all_services():
        logger.error("依赖服务检查失败，应用无法启动")
        sys.exit(1)


# 挂载子应用
app.mount("/import", import_service.app)
app.mount("/query", query_service.app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
