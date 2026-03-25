from pathlib import Path

from app.services.storage import AssetStorageService


class _FakeS3Client:
    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.puts: list[tuple[str, str, bytes, str]] = []

    def head_bucket(self, Bucket: str) -> None:
        if Bucket not in self.buckets:
            raise Exception("missing")

    def create_bucket(self, Bucket: str) -> None:
        self.buckets.add(Bucket)

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self.puts.append((Bucket, Key, Body, ContentType))


def test_asset_storage_service_persists_local_file(tmp_path) -> None:
    service = AssetStorageService(backend="local", output_dir=tmp_path)
    local_path, storage_url = service.persist_image("sample-article", "featured", b"image-bytes")
    assert Path(local_path).exists()
    assert storage_url.startswith("file:///")


def test_asset_storage_service_uploads_to_s3_and_returns_remote_url(tmp_path) -> None:
    service = AssetStorageService(backend="s3", output_dir=tmp_path, s3_client=_FakeS3Client())
    local_path, storage_url = service.persist_image("sample-article", "featured", b"image-bytes")
    assert Path(local_path).exists()
    assert storage_url.endswith(".png")
    assert "/article-assets/articles/sample-article/" in storage_url
