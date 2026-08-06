import json
import os
import tempfile
from pathlib import Path

from controller.rscript_utils import normalize_path_for_r, normalize_value_for_r, run_r_script


def run_plot(input_csv, options, manifest_path=None, r_script=None):
    """Run the R plotting workflow and return the manifest contents."""

    if manifest_path is None:
        manifest_path = os.path.join(tempfile.gettempdir(), "plotting_manifest.json")

    if r_script is None:
        r_script = Path(__file__).resolve().parents[1] / "rfishbase" / "plotting_workflow.R"

    options_path = None
    temp_dir = None

    try:
        temp_dir = tempfile.mkdtemp(prefix="ert_plotting_", dir=tempfile.gettempdir())
        options_path = os.path.join(temp_dir, "options.json")
        normalized_options = normalize_value_for_r(options)

        with open(options_path, "w", encoding="utf-8") as handle:
            json.dump(normalized_options, handle, indent=2)

        # Normalize all paths to forward slashes to prevent R from
        # interpreting backslash escape sequences (e.g. \U in \Users)
        # as Unicode escapes when parsing command-line arguments.
        r_script_str = normalize_path_for_r(r_script)
        input_csv_str = normalize_path_for_r(input_csv)
        options_path_str = normalize_path_for_r(options_path)
        manifest_path_str = normalize_path_for_r(manifest_path)

        run_r_script(
            [r_script_str, input_csv_str, options_path_str, manifest_path_str],
            cwd=normalize_path_for_r(Path(r_script).resolve().parent.parent),
        )

        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        return manifest

    except FileNotFoundError as exc:
        raise RuntimeError("Rscript is not available on PATH.") from exc
    except RuntimeError as exc:
        # Include R script stderr/stdout in the error for debugging
        details = str(exc)
        if hasattr(exc, "__cause__") and exc.__cause__ is not None:
            cause = exc.__cause__
            if hasattr(cause, "stderr") and cause.stderr:
                details += f"\nR stderr: {cause.stderr.strip()}"
            if hasattr(cause, "stdout") and cause.stdout:
                details += f"\nR stdout: {cause.stdout.strip()}"
        raise RuntimeError(details) from exc
    finally:
        if temp_dir and os.path.exists(temp_dir):
            for file_name in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)