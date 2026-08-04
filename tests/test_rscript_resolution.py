import os
import unittest
from pathlib import Path

from controller.rscript_utils import resolve_rscript_command


class RScriptResolutionTests(unittest.TestCase):
    def test_resolve_rscript_command_finds_installed_executable(self):
        command = resolve_rscript_command()

        self.assertIsNotNone(command)
        self.assertGreaterEqual(len(command), 1)
        self.assertIn(os.path.basename(command[0]), {"Rscript", "Rscript.exe"})
        self.assertTrue(Path(command[0]).exists())


if __name__ == "__main__":
    unittest.main()
