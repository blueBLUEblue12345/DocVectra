import os

# 设置 HuggingFace 离线模式，使用本地缓存（必须在导入 BGEM3EmbeddingFunction 之前设置）
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from processor.import_processor.base import setup_logging
from processor.import_processor.config import get_config

setup_logging()

# 模型单例对象，避免重复初始化
_bge_m3_ef = None

def get_bge_m3_ef():
    """
    获取BGE-M3模型单例对象，自动加载环境变量配置
    :return: 初始化完成的BGEM3EmbeddingFunction实例
    """
    global _bge_m3_ef
    if _bge_m3_ef is not None:
        return _bge_m3_ef

    # 从 ImportConfig 加载配置（已从.env读取）
    config = get_config()
    # 使用本地路径加载模型（反斜杠转正斜杠，避免 HF repo id 校验报错）
    model_name = config.bge_m3_path.replace("\\", "/")
    device = config.bge_device
    use_fp16 = config.bge_fp16

    # 如果模型没有被提前下载，会自动下载
    _bge_m3_ef = BGEM3EmbeddingFunction(
        model_name=model_name,
        device=device,
        use_fp16=use_fp16
    )
    return _bge_m3_ef

def generate_embeddings(texts ):
    """
    为文本生成向量嵌入
    :param texts: 要生成嵌入的文本列表
    :return: 包含dense和sparse向量的字典
    """
    model = get_bge_m3_ef()
    embeddings = model.encode_documents(texts)
    processed_sparse = []
    for i in range(len(texts)):
        sparse_indices = embeddings["sparse"].indices[embeddings["sparse"].indptr[i]:embeddings["sparse"].indptr[i+1]].tolist()
        sparse_data = embeddings["sparse"].data[embeddings["sparse"].indptr[i]:embeddings["sparse"].indptr[i+1]].tolist()
        sparse_dict = {k: v for k, v in zip(sparse_indices,sparse_data)}
        processed_sparse.append(sparse_dict)

    return {
        "dense": [emb.tolist() for emb in embeddings["dense"]],
        "sparse": processed_sparse
    }