import json
import os
import subprocess
import tempfile
from pathlib import Path


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

        with open(options_path, "w", encoding="utf-8") as handle:
            json.dump(options, handle, indent=2)

        subprocess.run(
            ["Rscript", str(r_script), input_csv, options_path, manifest_path],
            check=True,
            cwd=str(Path(r_script).resolve().parent.parent),
            capture_output=True,
            text=True,
        )

        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        return manifest

    except FileNotFoundError as exc:
        raise RuntimeError("Rscript is not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"R plotting workflow failed: {exc.stderr or exc.stdout}") from exc
    finally:
        if temp_dir and os.path.exists(temp_dir):
            for file_name in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)