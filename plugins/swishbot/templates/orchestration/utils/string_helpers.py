"""String Helpers.

Utility functions for string manipulation used across the orchestration layer.
"""

import re


def to_snake_case(s: str) -> str:
    """Convert a string to snake_case.

    Handles PascalCase, camelCase, and non-alphanumeric characters.
    """
    s = re.sub(r"[\W]+", "_", s)
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower().strip("_")
