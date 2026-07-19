from config import Settings


def test_cors_origin_list() -> None:
    settings = Settings(cors_origins="http://a.local, http://b.local")
    assert settings.cors_origin_list == ["http://a.local", "http://b.local"]


def test_jwks_and_issuer() -> None:
    settings = Settings(
        keycloak_url="http://keycloak:8080",
        keycloak_issuer="http://localhost:8080",
        keycloak_realm="acme",
    )
    assert "realms/acme" in settings.jwks_url
    assert settings.issuer.endswith("/realms/acme")
