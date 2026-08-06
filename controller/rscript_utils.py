import os
import shutil
import subprocess
from pathlib import Path


REQUIRED_R_PACKAGES = (
    "jsonlite",
    "dplyr",
    "rfishbase",
    "survival",
    "ggsurvfit",
    "ggplot2",
    "readxl",
)


def normalize_path_for_r(path_value):
    """Convert Windows backslashes to forward slashes for safe R argument parsing."""
    if path_value is None:
        return None
    if isinstance(path_value, Path):
        path_value = str(path_value)
    if isinstance(path_value, str):
        return path_value.replace("\\", "/")
    return path_value


def normalize_value_for_r(value):
    """Recursively normalize path-like strings in nested data before handing them to R."""
    if isinstance(value, dict):
        return {key: normalize_value_for_r(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_value_for_r(item) for item in value]
    if isinstance(value, tuple):
        return tuple(normalize_value_for_r(item) for item in value)
    if isinstance(value, Path):
        return normalize_path_for_r(value)
    if isinstance(value, str):
        return normalize_path_for_r(value)
    return value


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


def get_required_r_packages():
    """Return the R package list declared by the project requirements file."""
    requirements_path = Path(__file__).resolve().parents[1] / "rfishbase" / "requirements.R"
    packages = []

    if requirements_path.exists():
        for line in requirements_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("install.packages"):
                continue
            packages.append(stripped.split("#", 1)[0].strip())

    if packages:
        return tuple(packages)
    return REQUIRED_R_PACKAGES


def install_missing_r_packages(packages=None):
    """Attempt to install any missing R packages non-interactively."""
    command = ensure_rscript_available()
    package_list = tuple(packages or get_required_r_packages())
    if not package_list:
        return

    install_expr = (
        "options(repos = c(CRAN = 'https://cloud.r-project.org')); "
        "install.packages(c({}), quiet = TRUE, Ncpus = 1L)"
    ).format(", ".join(f'"{package}"' for package in package_list))

    result = subprocess.run(
        command + ["--vanilla", "-e", install_expr],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or str(result)
        raise RuntimeError(
            "R workflow cannot start because required R packages are missing and automatic installation failed. "
            f"Install them manually with: install.packages(c({', '.join(f'\"{pkg}\"' for pkg in package_list)}))\n{details}"
        )


def ensure_r_packages_available():
    """Check that the project-declared R packages are installed in the selected R environment."""
    command = ensure_rscript_available()
    packages = get_required_r_packages()
    check_expr = (
        "required <- c({}); missing <- required[!(required %in% rownames(installed.packages()))]; "
        "if (length(missing) > 0) stop(paste('Missing R packages:', paste(missing, collapse=', ')), call.=FALSE)"
    ).format(", ".join(f'"{package}"' for package in packages))

    result = subprocess.run(
        command + ["--vanilla", "-e", check_expr],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        try:
            install_missing_r_packages(packages)
        except RuntimeError:
            raise

        verification = subprocess.run(
            command + ["--vanilla", "-e", check_expr],
            capture_output=True,
            text=True,
        )
        if verification.returncode != 0:
            details = verification.stderr.strip() or verification.stdout.strip() or str(verification)
            raise RuntimeError(
                "R workflow cannot start because required R packages are missing. "
                f"Install them with: install.packages(c({', '.join(f'\"{pkg}\"' for pkg in packages)}))\n{details}"
            )


def run_r_script(args, cwd=None):
    command = ensure_rscript_available()
    ensure_r_packages_available()
    normalized_args = [normalize_path_for_r(arg) for arg in args]
    try:
        return subprocess.run(
            command + ["--vanilla"] + list(normalized_args),
            cwd=normalize_path_for_r(cwd) if cwd else cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        details = stderr.strip() or stdout.strip() or str(exc)
        raise RuntimeError(f"R workflow failed: {details}") from exc
