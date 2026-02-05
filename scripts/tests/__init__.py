"""
AO World Engine - Test Package

This package contains modular test suites for comprehensive validation.

Modules:
- base.py: Base classes and utilities
- test_core.py: Core simulation tests (NPCs, buildings, districts)
- test_economy.py: Economic simulation tests
- test_social.py: Social dynamics tests
- test_npcs.py: NPC behavior and data tests
- test_infrastructure.py: Lua modules, plugins, handlers
- test_behavioral.py: AI decision-making tests
- test_comprehensive.py: File audit, consistency, coverage

Created: 2026-02-05
Version: 5.0
Total Tests: 517
"""

from .base import TestResult, BaseTestSuite, PROJECT_ROOT, DATA_DIR, CODEC_DIR, LOGS_DIR, AO_DIR

__version__ = "5.0"
__all__ = [
    "TestResult",
    "BaseTestSuite",
    "PROJECT_ROOT",
    "DATA_DIR",
    "CODEC_DIR",
    "LOGS_DIR",
    "AO_DIR",
]
