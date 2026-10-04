#!/usr/bin/env python3
"""Download the pinned local model and register this private MLX runtime."""
import json
import sys

from sunroom_paths import ai_config, data_dir

if sys.platform == "win32":
    raise SystemExit(
        "On-device MLX is Apple Silicon only. On Windows, choose Local server "
        "(LM Studio at http://127.0.0.1:1234/v1 is allowed) or Luna. "
        "Create and Play does not need this script."
    )

# Imported after the Windows exit so a PC without the Apple MLX stack still
# gets the guidance above instead of an ImportError.
from huggingface_hub import snapshot_download

config_dir = data_dir()
revision = "0e7ffd5c629ef7719d4cbc04069232580bfa9d9c"
model = config_dir / "Models" / "Qwen3.5-4B-4bit"
snapshot_download("mlx-community/Qwen3.5-4B-4bit", revision=revision, local_dir=model,
                  allow_patterns=["*.json", "*.jinja", "*.safetensors"])
config_dir.mkdir(parents=True, exist_ok=True)
config = {"python": sys.executable, "model": str(model), "revision": revision,
          "model_id": "mlx-community/Qwen3.5-4B-4bit"}
ai_config().write_text(json.dumps(config, indent=2) + "\n")
ai_config().chmod(0o600)
print("SUNROOM MLX ready:", model)
