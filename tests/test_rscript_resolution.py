import os
import unittest
from pathlib import Path

from controller.rscript_utils import normalize_path_for_r, resolve_rscript_command


class RScriptResolutionTests(unittest.TestCase):
    def test_resolve_rscript_command_finds_installed_executable(self):
        command = resolve_rscript_command()

        self.assertIsNotNone(command)
        self.assertGreaterEqual(len(command), 1)
        self.assertIn(os.path.basename(command[0]), {"Rscript", "Rscript.exe"})
        self.assertTrue(Path(command[0]).exists())

    def test_normalize_path_for_r_converts_windows_style_paths(self):
        windows_path = r"C:\Users\joeyg\OneDrive\Desktop\AZA\ERT-Manager\rfishbase\plotting_workflow.R"
        normalized = normalize_path_for_r(windows_path)

        self.assertEqual(normalized, "C:/Users/joeyg/OneDrive/Desktop/AZA/ERT-Manager/rfishbase/plotting_workflow.R")


if __name__ == "__main__":
    unittest.main()
