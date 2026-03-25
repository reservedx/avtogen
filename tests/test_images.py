import base64

from app.services.images import ImageGenerator


def test_image_generator_creates_three_assets() -> None:
    images = ImageGenerator().generate("Frequent urination with cystitis")
    assert len(images) == 3
    assert images[0]["is_featured"] is True


class _FakeImageItem:
    def __init__(self, b64_json: str) -> None:
        self.b64_json = b64_json


class _FakeImageResponse:
    def __init__(self, b64_json: str) -> None:
        self.data = [_FakeImageItem(b64_json)]


class _FakeImagesClient:
    def __init__(self, b64_json: str) -> None:
        self._b64_json = b64_json

    def generate(self, **_: object) -> _FakeImageResponse:
        return _FakeImageResponse(self._b64_json)


class _FakeGateway:
    def __init__(self, b64_json: str) -> None:
        self.image_model = "gpt-image-1"
        self.image_output_format = "webp"
        self.client = type("Client", (), {"images": _FakeImagesClient(b64_json)})()

    def generate_image_variants(self, article_title: str) -> list[dict]:
        return [
            {
                "prompt": f"Featured illustration for {article_title}",
                "alt_text": f"Featured illustration for {article_title}",
                "is_featured": True,
            }
        ]


def test_image_generator_saves_binary_asset(tmp_path) -> None:
    webp_b64 = base64.b64encode(b"fake-webp-bytes").decode("utf-8")
    generator = ImageGenerator(gateway=_FakeGateway(webp_b64), output_dir=tmp_path)
    images = generator.generate("Frequent urination with cystitis", "frequent-urination-cystitis")
    assert len(images) == 1
    assert images[0]["local_path"] is not None
    assert images[0]["storage_url"] is not None
    assert images[0]["local_path"].endswith(".webp")
