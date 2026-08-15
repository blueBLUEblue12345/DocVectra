import json
import threading
from minio import Minio
from processor.import_processor.config import ImportConfig

_minio_client = None
_init_lock = threading.Lock()


def get_minio_client():
    """获取 MinIO 客户端实例（懒加载，线程安全）"""
    global _minio_client

    if _minio_client is not None:
        return _minio_client

    with _init_lock:
        if _minio_client is not None:
            return _minio_client

        try:
            config = ImportConfig()

            _minio_client = Minio(
                endpoint=config.minio_endpoint,
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                secure=False
            )

            if not _minio_client.bucket_exists(config.minio_bucket):
                _minio_client.make_bucket(config.minio_bucket)

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
            _minio_client.set_bucket_policy(config.minio_bucket, json.dumps(policy))

        except Exception as e:
            print(f"Minio init failed: {e}")
            _minio_client = None

    return _minio_client


if __name__ == "__main__":
    client = get_minio_client()
    print(f"MinIO client: {client}")