import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]

def run_precompute_subprocess(
    *,
    force: bool = False,
    batch_size: Optional[int] = None,
) -> Tuple[int, Path]:
    """
    Spawn a detached process that executes the precompute_embeddings management command.
    Returns (pid, log_path) so callers can report tracking information. log_path will be None when logs are not captured.
    """
    cmd = [
        sys.executable,
        str(BASE_DIR / "manage.py"),
        "precompute_embeddings",
    ]
    if batch_size is not None:
        cmd.append(f"--batch-size={batch_size}")
    if force:
        cmd.append("--force")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )

    return proc.pid, None
