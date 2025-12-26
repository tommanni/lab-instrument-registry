import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def run_precompute_subprocess(
    *,
    force: bool = False,
    batch_size: Optional[int] = None,
) -> Tuple[int, Path]:
    """
    Spawn a detached process that executes the precompute_embeddings management command.
    Returns (pid, log_path) so callers can report tracking information. log_path will be None when logs are not captured.
    """
    # Create a unique log file for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"enrichment_run_{timestamp}.log"
    
    cmd = [
        sys.executable,
        str(BASE_DIR / "manage.py"),
        "precompute_embeddings",
    ]

    if batch_size is not None:
        cmd.append(f"--batch-size={batch_size}")
    if force:
        cmd.append("--force")

    f_out = open(log_file, "w")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=f_out,     # stdout goes to file
            stderr=subprocess.STDOUT, # stderr also goes to the SAME file
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except Exception:
        f_out.close()
        raise

    f_out.close()

    return proc.pid, log_file
