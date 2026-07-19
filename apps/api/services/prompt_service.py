from dataclasses import dataclass
from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass(frozen=True)
class CompiledPrompt:
    name: str
    version: int
    text: str
    labels: list[str]


class PromptService:
    def __init__(self, prompts_dir: Path = PROMPTS_DIR) -> None:
        self.prompts_dir = prompts_dir

    def load_raw(self, filename: str = "relay-system.yaml") -> dict:
        path = self.prompts_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Prompt file {filename} must be a mapping")
        for required in ("name", "version", "template", "labels"):
            if required not in data:
                raise ValueError(f"Prompt {filename} missing '{required}'")
        if not isinstance(data["version"], int) or data["version"] < 1:
            raise ValueError(f"Prompt {filename} version must be a positive integer")
        return data

    def compile_system(self, *, user_roles: str) -> CompiledPrompt:
        raw = self.load_raw()
        text = str(raw["template"]).format(user_roles=user_roles)
        return CompiledPrompt(
            name=str(raw["name"]),
            version=int(raw["version"]),
            text=text,
            labels=list(raw.get("labels") or []),
        )


prompt_service = PromptService()
