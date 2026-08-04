import os
import shutil
import subprocess
from pathlib import Path


def resolve_rscript_command():
    """Return the best available Rscript command for this machine."""
    candidates = []

    explicit = os.environ.get("RSCRIPT_PATH")
    if explicit:
        candidates.append(explicit)

    if shutil.which("Rscript"):
        candidates.append(shutil.which("Rscript"))

    if shutil.which("R"):
        candidates.append(shutil.which("R"))

    # Common Windows installations when R is present but not on PATH.
    common_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R" / "R-4.6.1" / "bin" / "x64" / "Rscript.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R" / "R-4.4.0" / "bin" / "x64" / "Rscript.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R" / "R-4.6.1" / "bin" / "Rscript.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R" / "R-4.4.0" / "bin" / "Rscript.exe",
        Path("C:/Program Files/R/R-4.6.1/bin/x64/Rscript.exe"),
        Path("C:/Program Files/R/R-4.4.0/bin/x64/Rscript.exe"),
        Path("C:/Program Files/R/R-4.6.1/bin/Rscript.exe"),
        Path("C:/Program Files/R/R-4.4.0/bin/Rscript.exe"),
    ]
    for path in common_paths:
        if path.exists():
            candidates.append(str(path))

    # De-duplicate while preserving order.
    seen = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            if os.path.exists(candidate):
                return [candidate]

    return None


def ensure_rscript_available():
    command = resolve_rscript_command()
    if command is None:
        raise RuntimeError(
            "Rscript was not found. Install R and ensure Rscript is available on PATH or set RSCRIPT_PATH."
        )
    return command


def run_r_script(args, cwd=None):
    command = ensure_rscript_available()
    try:
        return subprocess.run(
            command + list(args),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        details = stderr.strip() or stdout.strip() or str(exc)
        raise RuntimeError(f"R workflow failed: {details}") from exc
