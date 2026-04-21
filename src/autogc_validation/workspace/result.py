# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 14:31:01 2026

@author: aengstrom
"""
from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path
import json
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

_STATE_FILENAME = ".workspace_state.json"


def _serialize_summary(summary: Optional[dict]) -> Optional[dict]:
    """Convert a file-move summary dict to JSON-serializable form."""
    if summary is None:
        return None
    return {
        key: {"count": val[0], "files": val[1]}
        for key, val in summary.items()
    }


def _deserialize_summary(data: Optional[dict]) -> Optional[dict]:
    """Convert a stored summary back to the (count, list) tuple format."""
    if data is None:
        return None
    return {
        key: (val["count"], val["files"])
        for key, val in data.items()
    }


@dataclass
class WorkspaceResult:
    """Record of a workspace initialization run.

    Each field captures the result of one step. A value of None
    means the step was skipped. The record can be saved to and
    loaded from disk to survive kernel restarts.
    """
    base_dir: Optional[Path] = None
    data_dir: Optional[Path] = None
    unzipped: Optional[list[Path]] = None
    documents: Optional[list[Path]] = None
    dat_summary: Optional[dict] = None
    tx1_summary: Optional[dict] = None
    week_counts: Optional[dict[str, int]] = None
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    step_timestamps: dict[str, str] = field(default_factory=dict)

    def save(self) -> Path:
        """Save the workspace state to .workspace_state.json in base_dir.

        Returns:
            Path to the saved state file.

        Raises:
            ValueError: If base_dir is not set.
        """
        if self.base_dir is None:
            raise ValueError("Cannot save: base_dir is not set")

        state = {
            "base_dir": str(self.base_dir),
            "data_dir": str(self.data_dir) if self.data_dir else None,
            "unzipped": [str(p) for p in self.unzipped] if self.unzipped else None,
            "documents": [str(p) for p in self.documents] if self.documents else None,
            "dat_summary": _serialize_summary(self.dat_summary),
            "tx1_summary": _serialize_summary(self.tx1_summary),
            "week_counts": self.week_counts,
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "step_timestamps": self.step_timestamps,
            "saved_at": datetime.now().isoformat(),
        }

        state_path = self.base_dir / _STATE_FILENAME
        state_path.write_text(json.dumps(state, indent=2))
        logger.info("Workspace state saved to %s", state_path)
        return state_path

    @classmethod
    def load(cls, workspace_dir: Union[str, Path]) -> "WorkspaceResult":
        """Load workspace state from a previously saved .workspace_state.json.

        Args:
            workspace_dir: Path to the monthly validation folder
                (e.g. RB202601v1/).

        Returns:
            WorkspaceResult restored from disk.

        Raises:
            FileNotFoundError: If no state file exists in the directory.
        """
        state_path = Path(workspace_dir) / _STATE_FILENAME
        if not state_path.exists():
            raise FileNotFoundError(f"No workspace state found at {state_path}")

        data = json.loads(state_path.read_text())

        result = cls(
            base_dir=Path(data["base_dir"]),
            data_dir=Path(data["data_dir"]) if data.get("data_dir") else None,
            unzipped=[Path(p) for p in data["unzipped"]] if data.get("unzipped") else None,
            documents=[Path(p) for p in data["documents"]] if data.get("documents") else None,
            dat_summary=_deserialize_summary(data.get("dat_summary")),
            tx1_summary=_deserialize_summary(data.get("tx1_summary")),
            week_counts=data.get("week_counts"),
            steps_completed=data.get("steps_completed", []),
            errors=data.get("errors", []),
            step_timestamps=data.get("step_timestamps", {}),
        )
        logger.info("Workspace state loaded from %s", state_path)
        return result