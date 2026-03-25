from app.services.platform import WordPressAdapter


def test_wordpress_adapter_builds_base_api() -> None:
    adapter = WordPressAdapter()
    assert "/wp-json/wp/v2" in adapter.base_api
