"""
Base classes and utilities for the AO World Engine test suite.

Created: 2026-02-05
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODEC_DIR = DATA_DIR / "codec_chunks"
LOGS_DIR = PROJECT_ROOT / "logs"
AO_DIR = PROJECT_ROOT / "ao-processes"

LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class TestResult:
    """Result of a single test."""
    category: str
    test_name: str
    method: str  # schema, completeness, integration
    passed: bool
    message: str
    details: Dict[str, Any] = None
    severity: str = "info"  # info, warning, critical


class BaseTestSuite:
    """Base class for all test suites."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.data_cache: Dict[str, Any] = {}
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "by_category": defaultdict(lambda: {"passed": 0, "failed": 0})
        }
    
    def load_codec(self, name: str) -> Dict[str, Any]:
        """Load codec JSON file with caching."""
        if name not in self.data_cache:
            path = CODEC_DIR / f"{name}.json"
            if path.exists():
                with open(path) as f:
                    self.data_cache[name] = json.load(f)
            else:
                self.data_cache[name] = {}
        return self.data_cache[name]
    
    def record(self, result: TestResult):
        """Record a test result."""
        self.results.append(result)
        self.stats["total"] += 1
        if result.passed:
            self.stats["passed"] += 1
            self.stats["by_category"][result.category]["passed"] += 1
        else:
            self.stats["failed"] += 1
            self.stats["by_category"][result.category]["failed"] += 1
            if result.severity == "warning":
                self.stats["warnings"] += 1
    
    def run_all(self):
        """Override in subclasses to run tests."""
        raise NotImplementedError("Subclasses must implement run_all()")
    
    def get_results(self):
        """Return results and stats."""
        return self.results, self.stats
