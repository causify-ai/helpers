"""
Shared utilities for pytest testing scripts.

For architecture overview, see pytest_testing_system.README.md
"""

from typing import Dict, Tuple

# Build configurations: name -> (docker_engine, use_docker_cmd).
BUILD_CONFIG: Dict[str, Tuple[str, bool]] = {
    "docker": ("docker", False),
    "apple": ("apple", False),
    "dev_container": ("docker", True),
}
