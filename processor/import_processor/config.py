"""
导入流程配置管理模块

集中管理所有配置项，支持环境变量覆盖
"""

from dataclasses import dataclass, field
from typing import Set, Optional
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class ImportConfig:
    """导入流程配置"""

    # ==================== 文档处理配置 ====================
    max_content_length: int = 2000      # 切片最大长度
    img_content_length: int = 200       # 图片上下文最大长度
    min_content_length: int = 500       # 合并短内容的最小长度
    overlap_sentences: int = 1          # 句子级切分时重叠句数
    item_name_chunk_k: int = 3          # 商品名识别时使用的切片数量
    item_name_chunk_size: int = 2500    # 商品名识别时使用的切片内容长度

    # 支持的图片扩展名
    image_extensions: Set[str] = field(
        default_factory=lambda: {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    )
    # ==================== MinerU配置 ====================
    mineru_api_token: str = field(
        default_factory=lambda: os.getenv("MINERU_API_TOKEN", "")
    )
    mineru_base_url: str = field(
        default_factory=lambda: os.getenv("MINERU_BASE_URL", "")
    )
    # ==================== LLM 配置 ====================
    openai_api_base: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_BASE", "")
    )
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    vl_model: str = field(
        default_factory=lambda: os.getenv("VL_MODEL", "")
    )
    item_model: str = field(
        default_factory=lambda: os.getenv("ITEM_MODEL", "")
    )
    default_model: str = field(
        default_factory=lambda: os.getenv("MODEL", "")
    )
    # LLM 调用别名（供 query_processor 节点使用）
    api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    base_url: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_BASE", "")
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.1"))
    )

    # ==================== BGE Embedding 配置 ====================
    bge_m3_path: str = field(
        default_factory=lambda: os.getenv("BGE_M3_PATH", "")
    )
    bge_m3: str = field(
        default_factory=lambda: os.getenv("BGE_M3", "")
    )
    bge_device: str = field(
        default_factory=lambda: os.getenv("BGE_DEVICE", "cpu")
    )
    bge_fp16: bool = field(
        default_factory=lambda: os.getenv("BGE_FP16", "False").lower() in ("true", "1", "yes")
    )
    bge_reranker_large: str = field(
        default_factory=lambda: os.getenv("BGE_RERANKER_LARGE", "")
    )
    bge_reranker_device: str = field(
        default_factory=lambda: os.getenv("BGE_RERANKER_DEVICE", "cpu")
    )
    bge_reranker_fp16: bool = field(
        default_factory=lambda: os.getenv("BGE_RERANKER_FP16", "0").lower() in ("true", "1", "yes")
    )

    # ==================== Milvus 配置 ====================
    milvus_url: str = field(
        default_factory=lambda: os.getenv("MILVUS_URL", "")
    )
    chunks_collection: str = field(
        default_factory=lambda: os.getenv("CHUNKS_COLLECTION", "")
    )
    item_name_collection: str = field(
        default_factory=lambda: os.getenv("ITEM_NAME_COLLECTION", "")
    )

    # ==================== MinIO 配置 ====================
    minio_endpoint: str = field(
        default_factory=lambda: os.getenv("MINIO_ENDPOINT", "")
    )
    minio_access_key: str = field(
        default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "")
    )
    minio_secret_key: str = field(
        default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "")
    )
    minio_bucket: str = field(
        default_factory=lambda: os.getenv("MINIO_BUCKET_NAME", "")
    )
    minio_img_dir: str = field(
        default_factory=lambda: os.getenv("MINIO_IMG_DIR", "")
    )
    minio_secure: bool = False

    # ==================== 向量配置 ====================
    embedding_dim: int = field(
        default_factory=lambda: int(os.getenv("EMBEDDING_DIM", "1024"))
    )
    embedding_batch_size: int = 8

    # ==================== 速率限制 ====================
    requests_per_minute: int = 15       # 图片总结 API 速率限制

    @classmethod
    def from_env(cls) -> "ImportConfig":
        """从环境变量加载配置"""
        return cls()

    def get_minio_base_url(self) -> str:
        """获取 MinIO 基础 URL"""
        protocol = "https://" if self.minio_secure else "http://"
        return protocol + f"{self.minio_endpoint}"


# ==================== 全局单例 ====================
_config: Optional[ImportConfig] = None


def get_config() -> ImportConfig:
    """获取配置单例"""
    global _config
    if _config is None:
        _config = ImportConfig.from_env()
    return _config