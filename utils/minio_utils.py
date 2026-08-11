import json
from minio import Minio
from processor.import_processor.config import ImportConfig

# 初始化 MinIO 客户端
minio_client = None

try:
    # 加载配置
    config = ImportConfig()
    
    minio_client = Minio(
        endpoint=config.minio_endpoint,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        secure=False
    )
    # secure=False 是否启用HTTPS加密连接；False=用HTTP，True=用HTTPS；本地/内网部署一律写False
    if not minio_client.bucket_exists(config.minio_bucket):
        minio_client.make_bucket(config.minio_bucket)
    # 设置存储桶策略为 Public Read (只读权限开放给匿名用户)
    # 这样前端可以直接通过 URL 访问图片，而不需要预签名 URL
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{config.minio_bucket}/*"]
            }
        ]
    }
    minio_client.set_bucket_policy(config.minio_bucket, json.dumps(policy))
except Exception as e:
    print(f"Minio init failed: {e}")
    minio_client = None

def get_minio_client():
    return minio_client

if __name__ == "__main__":
    minio_client = get_minio_client()