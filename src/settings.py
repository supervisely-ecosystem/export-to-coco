"""Export options from the modal window, parsed and validated once at startup."""

from __future__ import annotations

import ast
import os
from collections.abc import Mapping
from dataclasses import dataclass

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    export_images: bool
    only_annotated: bool
    dataset_ids: tuple[int, ...] | None  # None: every dataset of the project, nested ones included
    with_captions: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Settings:
        """Read `modal.state.*` variables the platform sets from the modal window."""

        def state(key: str, default: str) -> str:
            return env.get(f"modal.state.{key}", default).strip()

        output = state("selectedOutput", "images")
        if output not in ("images", "annotations"):
            raise ValueError(f"selectedOutput must be 'images' or 'annotations', got {output!r}")

        image_filter = state("selectedFilter", "all")
        if image_filter not in ("all", "annotated"):
            raise ValueError(f"selectedFilter must be 'all' or 'annotated', got {image_filter!r}")

        dataset_ids = None
        if not _parse_bool(state("allDatasets", "true")):
            dataset_ids = _parse_ids(state("datasets", "[]"))
            if not dataset_ids:
                raise ValueError("Select at least one dataset or enable 'Export all datasets'")

        return cls(
            export_images=output == "images",
            only_annotated=image_filter == "annotated",
            dataset_ids=dataset_ids,
            with_captions=_parse_bool(state("captions", "false")),
        )


def _parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise ValueError(f"Expected a boolean, got {value!r}")


def _parse_ids(value: str) -> tuple[int, ...]:
    parsed = ast.literal_eval(value) if value else []
    if isinstance(parsed, int):
        parsed = [parsed]
    return tuple(int(item) for item in parsed)
