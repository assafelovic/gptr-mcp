"""Load output presets and apply them before report generation.

Loads presets from the volume-mounted config/output_presets.py.
Before calling researcher.write_report(), call apply_preset() to
set TOTAL_WORDS env var and get the custom_prompt for the output type.
"""

import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_PRESETS = {
    "summary": {"total_words": 200, "prompt": "Write a concise bullet-point summary of the key findings."},
    "briefing": {"total_words": 600, "prompt": "Write an executive briefing with key findings and conclusions."},
    "report": {"total_words": 1200, "prompt": None},
    "deep_report": {"total_words": 2500, "prompt": None},
    "raw_context": {"total_words": None, "prompt": None},
}

VALID_OUTPUT_TYPES = {"summary", "briefing", "report", "deep_report", "raw_context"}


def _load_presets():
    """Load presets from volume-mounted config file, fall back to defaults."""
    config_path = os.environ.get("OUTPUT_PRESETS_PATH", "/app/config/output_presets.py")
    if os.path.exists(config_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("output_presets", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logger.info(f"Loaded output presets from {config_path}")
        return module.PRESETS
    else:
        logger.warning(f"Presets config not found at {config_path}, using defaults")
        return DEFAULT_PRESETS


PRESETS = _load_presets()


def validate_output_type(output_type: str) -> str:
    """Validate and return normalized output type. Raises ValueError for unknown types."""
    if output_type not in VALID_OUTPUT_TYPES:
        raise ValueError(
            f"Unknown output_type '{output_type}'. "
            f"Valid types: {', '.join(sorted(VALID_OUTPUT_TYPES))}"
        )
    return output_type


def apply_preset(output_type: str) -> str | None:
    """Apply preset for the given output type.

    Sets TOTAL_WORDS env var and returns custom_prompt (or None for default).
    Call this BEFORE researcher.write_report().

    Returns:
        custom_prompt string, or None to use GPT-Researcher's default prompt.
    """
    validate_output_type(output_type)
    preset = PRESETS.get(output_type, DEFAULT_PRESETS.get(output_type))

    if preset["total_words"] is not None:
        os.environ["TOTAL_WORDS"] = str(preset["total_words"])
        logger.info(f"Set TOTAL_WORDS={preset['total_words']} for output_type={output_type}")

    return preset.get("prompt")


def is_paginated_type(output_type: str) -> bool:
    """Return True if this output type should be paginated."""
    return output_type in ("report", "deep_report", "raw_context")


def is_raw_context(output_type: str) -> bool:
    """Return True if this output type skips report generation."""
    return output_type == "raw_context"
