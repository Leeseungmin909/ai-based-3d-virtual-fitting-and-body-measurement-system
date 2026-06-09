import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# SMPL-X model files are licensed assets and are not committed to Git.
# Override this location with the SMPLX_DIR environment variable when needed.
SMPLX_DIR = Path(
    os.getenv("SMPLX_DIR", str(PROJECT_ROOT / "weights" / "smplx"))
).resolve()
SMPLX_MODEL_DIR = SMPLX_DIR / "smplx"
SMPLX_UV_OBJ = SMPLX_MODEL_DIR / "smplx_uv_2021.obj"
SMPLX_UV_PNG = SMPLX_MODEL_DIR / "smplx_uv_2021.png"
