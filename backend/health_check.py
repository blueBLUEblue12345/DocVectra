"""
依赖服务健康检查模块

在应用启动时检查所有依赖服务是否就绪
"""
import socket
import sys
from typing import Tuple

from tools.logger import logger


def check_service(host: str, port: int, service_name: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    检查服务是否可连接

    Args:
        host: 服务主机地址
        port: 服务端口
        service_name: 服务名称（用于日志）
        timeout: 连接超时时间（秒）

    Returns:
        (是否成功, 错误信息)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            logger.info(f"✓ {service_name} 服务就绪 ({host}:{port})")
            return True, ""
        else:
            return False, f"{service_name} 服务不可达 ({host}:{port})"
    except Exception as e:
        return False, f"{service_name} 连接失败: {str(e)}"


def check_milvus() -> Tuple[bool, str]:
    """检查 Milvus 向量数据库"""
    import os
    milvus_url = os.getenv("MILVUS_URL", "http://localhost:19530")

    # 解析 host:port
    if "://" in milvus_url:
        milvus_url = milvus_url.split("://", 1)[1]
    parts = milvus_url.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 19530

    return check_service(host, port, "Milvus")


def check_mongodb() -> Tuple[bool, str]:
    """检查 MongoDB 文档数据库"""
    import os
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")

    # 解析 host:port
    if "://" in mongo_url:
        mongo_url = mongo_url.split("://", 1)[1]
    if "/" in mongo_url:
        mongo_url = mongo_url.split("/", 1)[0]
    parts = mongo_url.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 27017

    return check_service(host, port, "MongoDB")


def check_minio() -> Tuple[bool, str]:
    """检查 MinIO 对象存储"""
    import os
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")

    parts = minio_endpoint.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 9000

    return check_service(host, port, "MinIO")


def check_redis() -> Tuple[bool, str]:
    """检查 Redis 缓存服务"""
    import os
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # 解析 host:port
    if "://" in redis_url:
        redis_url = redis_url.split("://", 1)[1]
    if "/" in redis_url:
        redis_url = redis_url.split("/", 1)[0]
    parts = redis_url.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 6379

    return check_service(host, port, "Redis")


def check_all_services() -> bool:
    """
    检查所有依赖服务

    Returns:
        是否所有服务都就绪
    """
    logger.info("=" * 60)
    logger.info("开始检查依赖服务...")
    logger.info("=" * 60)

    checks = [
        check_milvus,
        check_mongodb,
        check_minio,
        check_redis,
    ]

    all_passed = True
    failed_services = []

    for check_func in checks:
        try:
            success, error_msg = check_func()
            if not success:
                all_passed = False
                failed_services.append(error_msg)
                logger.error(f"✗ {error_msg}")
        except Exception as e:
            all_passed = False
            error_msg = f"{check_func.__name__} 检查失败: {str(e)}"
            failed_services.append(error_msg)
            logger.error(f"✗ {error_msg}")

    logger.info("=" * 60)

    if all_passed:
        logger.info("✓ 所有依赖服务检查通过")
        logger.info("=" * 60)
    else:
        logger.error("✗ 部分依赖服务未就绪")
        logger.error("请确保以下服务已启动：")
        for msg in failed_services:
            logger.error(f"  - {msg}")
        logger.error("=" * 60)
        logger.error("提示：使用 Docker 快速启动依赖服务：")
        logger.error("  docker run -d --name milvus -p 19530:19530 milvusdb/milvus:v2.4.0")
        logger.error("  docker run -d --name mongodb -p 27017:27017 mongo:7.0")
        logger.error("  docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio")
        logger.error("  docker run -d --name redis -p 6379:6379 redis:7-alpine")
        logger.error("=" * 60)

    return all_passed
