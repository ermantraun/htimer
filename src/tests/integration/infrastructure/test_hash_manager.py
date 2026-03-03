from application.user import interfaces as user_interfaces


def test_generate_and_verify(
    infra_hash_generator: user_interfaces.HashGenerator,
    infra_hash_verifier: user_interfaces.HashVerifier,
):
    manager = infra_hash_generator

    hashed = manager.generate("secret")

    assert isinstance(hashed, str)
    assert infra_hash_verifier.verify("secret", hashed) is True
    assert infra_hash_verifier.verify("wrong", hashed) is False


def test_compatibility_methods(
    infra_hash_generator: user_interfaces.HashGenerator,
):
    manager = infra_hash_generator

    assert hasattr(manager, "generate_hash")
    assert hasattr(manager, "verify_hash")

    hashed = manager.generate_hash("secret")  # type: ignore[attr-defined]

    assert manager.verify_hash("secret", hashed) is True  # type: ignore[attr-defined]
