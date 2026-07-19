from services.prompt_service import PromptService


def test_prompt_has_version_and_production_label() -> None:
    service = PromptService()
    raw = service.load_raw()
    assert raw["version"] >= 1
    assert "production" in raw["labels"]
    assert "{user_roles}" in raw["template"] or "user_roles" in raw["variables"]


def test_compile_system_injects_roles() -> None:
    compiled = PromptService().compile_system(user_roles="sales_user")
    assert "sales_user" in compiled.text
    assert compiled.version >= 1
