from app.services.images import ImageGenerator


def test_image_generator_creates_three_assets() -> None:
    images = ImageGenerator().generate("Frequent urination with cystitis")
    assert len(images) == 3
    assert images[0]["is_featured"] is True
