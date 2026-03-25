from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from app.config import settings


class AssetStorageService:
    def __init__(
        self,
        backend: str | None = None,
        output_dir: str | Path | None = None,
        s3_client: BaseClient | None = None,
    ) -> None:
        self.backend = (backend or settings.asset_storage_backend).lower()
        self.output_dir = Path(output_dir or settings.asset_storage_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.bucket = settings.s3_bucket
        self._s3_client = s3_client

    @property
    def s3_enabled(self) -> bool:
        return self.backend in {"s3", "hybrid"}

    @property
    def s3_client(self) -> BaseClient:
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
            )
        return self._s3_client

    def persist_image(self, article_slug: str, image_role: str, image_bytes: bytes) -> tuple[str, str]:
        local_path = self._write_local(article_slug, image_role, image_bytes)
        local_url = Path(local_path).resolve().as_uri()
        if not self.s3_enabled:
            return local_path, local_url
        try:
            key = self._object_key(article_slug, Path(local_path).name)
            self._ensure_bucket()
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=image_bytes,
                ContentType="image/png",
            )
            return local_path, self._public_url(key)
        except Exception:
            return local_path, local_url

    def _write_local(self, article_slug: str, image_role: str, image_bytes: bytes) -> str:
        article_dir = self.output_dir / article_slug
        article_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{image_role}-{uuid4().hex[:10]}.png"
        path = article_dir / filename
        path.write_bytes(image_bytes)
        return str(path.resolve())

    def _object_key(self, article_slug: str, filename: str) -> str:
        return f"articles/{article_slug}/{filename}"

    def _public_url(self, key: str) -> str:
        base = settings.s3_public_base_url or settings.s3_endpoint_url.rstrip("/")
        return f"{base}/{self.bucket}/{key}"

    def _ensure_bucket(self) -> None:
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.s3_client.create_bucket(Bucket=self.bucket)
