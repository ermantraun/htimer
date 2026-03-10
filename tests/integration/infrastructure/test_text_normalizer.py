from htimer.application import common_interfaces


def test_normalize_removes_emoji_and_symbols(
    infra_text_normalizer: common_interfaces.TextNormalizer,
):
    result = infra_text_normalizer.normalize("  Привет🙂!!!   Hello@@@  ")

    assert result == "Привет Hello"
