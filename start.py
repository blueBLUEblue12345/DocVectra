"""
DocVectra 一键启动脚本

功能：
1. 检查依赖服务（Milvus/MongoDB/MinIO/Redis）是否就绪
2. 启动后端服务（uvicorn）
3. 启动前端服务（npm run dev）
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000


def check_service(host: str, port: int, name: str, timeout: float = 3.0) -> bool:
    """检查 TCP 服务是否可连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def parse_url(url: str) -> tuple[str, int]:
    """从 URL 解析 host:port"""
    # 处理 redis:// 协议
    if url.startswith("redis://"):
        url = url.replace("redis://", "http://", 1)
    if "://" not in url:
        url = "http://" + url
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port
    # 处理 host:port 格式（如 MINIO_ENDPOINT）
    if port is None and ":" in url and "://" not in url:
        parts = url.rsplit(":", 1)
        if parts[1].isdigit():
            host, port = parts[0], int(parts[1])
    return host, port


def check_dependencies() -> list[tuple[str, bool]]:
    """检查所有依赖服务，返回 [(服务名, 是否就绪)]"""
    services = []

    # Milvus
    milvus_url = os.getenv("MILVUS_URL", "http://localhost:19530")
    host, port = parse_url(milvus_url)
    print(f"  [DEBUG] Milvus: {milvus_url} -> {host}:{port}")
    services.append(("Milvus", check_service(host, port, "Milvus")))

    # MongoDB
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    host, port = parse_url(mongo_url)
    print(f"  [DEBUG] MongoDB: {mongo_url} -> {host}:{port}")
    services.append(("MongoDB", check_service(host, port, "MongoDB")))

    # MinIO
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    host, port = parse_url(minio_endpoint)
    print(f"  [DEBUG] MinIO: {minio_endpoint} -> {host}:{port}")
    services.append(("MinIO", check_service(host, port, "MinIO")))

    # Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    host, port = parse_url(redis_url)
    print(f"  [DEBUG] Redis: {redis_url} -> {host}:{port}")
    services.append(("Redis", check_service(host, port, "Redis")))

    return services


def print_status(services: list[tuple[str, bool]]) -> bool:
    """打印服务状态，返回是否全部就绪"""
    print("\n" + "=" * 60)
    print("依赖服务状态检查")
    print("=" * 60)

    all_ok = True
    for name, ok in services:
        status = "✓ 就绪" if ok else "✗ 未就绪"
        print(f"  {name:12} {status}")
        if not ok:
            all_ok = False

    print("=" * 60)

    if not all_ok:
        print("\n部分服务未就绪，请先启动依赖服务：")
        print("  docker compose -f docker-compose.dev.yml up -d")
        print("  或手动启动: docker start milvus-standalone mongo minio redis\n")

    return all_ok


def start_backend():
    """启动后端服务"""
    print("\n启动后端服务...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", BACKEND_HOST,
        "--port", str(BACKEND_PORT),
        "--reload"
    ]
    return subprocess.Popen(cmd, cwd=PROJECT_ROOT)


def start_frontend():
    """启动前端服务"""
    print("启动前端服务...")
    frontend_dir = PROJECT_ROOT / "frontend"

    if not (frontend_dir / "node_modules").exists():
        print("  前端依赖未安装，正在安装...")
        subprocess.run(["cmd", "/c", "npm", "install"], cwd=frontend_dir, check=True)

    cmd = ["cmd", "/c", "npm", "run", "dev"]
    return subprocess.Popen(cmd, cwd=frontend_dir)


def wait_for_backend(timeout: int = 30) -> bool:
    """等待后端服务就绪"""
    print("等待后端服务就绪...")
    url = f"http://127.0.0.1:{BACKEND_PORT}/docs"
    start = time.time()

    while time.time() - start < timeout:
        try:
            resp = httpx.get(url, timeout=2)
            if resp.status_code == 200:
                print("  后端服务已就绪")
                return True
        except Exception:
            pass
        time.sleep(1)

    print("  后端服务启动超时")
    return False


def main():
    print("=" * 60)
    print("DocVectra 知识库系统 - 一键启动")
    print("=" * 60)

    # 1. 检查依赖服务
    services = check_dependencies()
    if not print_status(services):
        sys.exit(1)

    # 2. 启动后端
    backend_proc = start_backend()

    # 3. 等待后端就绪
    if not wait_for_backend():
        print("后端启动失败，请检查日志")
        backend_proc.terminate()
        sys.exit(1)

    # 4. 启动前端
    frontend_proc = start_frontend()

    # 5. 打印访问地址
    print("\n" + "=" * 60)
    print("启动完成！")
    print("=" * 60)
    print(f"  后端 API:    http://localhost:{BACKEND_PORT}/docs")
    print(f"  前端界面:    http://localhost:{FRONTEND_PORT}")
    print("\n按 Ctrl+C 停止所有服务")
    print("=" * 60 + "\n")

    # 6. 保持运行
    try:
        while True:
            # 检查子进程是否退出
            if backend_proc.poll() is not None:
                print("后端服务已退出")
                break
            if frontend_proc.poll() is not None:
                print("前端服务已退出")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait(timeout=5)
        frontend_proc.wait(timeout=5)
        print("所有服务已停止")


if __name__ == "__main__":
    main()
