#!/usr/bin/env python3
"""
Unit Test Suite for Deployment Pipeline Parity (dndwikis).
Prevents regressions, broken links, and phantom sessions across index, codex, critics, and reader files.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from verify_deployment_pipeline import verify_pipeline


class TestDeploymentPipeline(unittest.TestCase):
    def test_pipeline_verification_passes(self):
        """The deployment pipeline verification gate must pass with zero critical errors."""
        passed = verify_pipeline()
        self.assertTrue(passed, "Pre-deployment pipeline verification gate failed!")


if __name__ == "__main__":
    unittest.main()
