"""
Simulation state management.

Manages simulation state locally via JSON files with optional sync to Convex.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# Default state file location
STATE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "simulation"
STATE_FILE = STATE_DIR / "state.json"

SimulationStatus = Literal["ready", "training", "predicting", "advancing"]


@dataclass
class SimulationState:
    """Represents the current state of a season simulation."""

    name: str
    target_season: int
    training_seasons: list[int]
    current_week: int  # 0 = pre-season, 1-18 = active
    status: SimulationStatus
    last_trained_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.utcnow().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationState":
        """Create instance from dictionary."""
        return cls(**data)

    def advance_to_week(self, week: int) -> None:
        """Advance simulation to specified week.

        Args:
            week: Target week (must be > current_week and <= 18).

        Raises:
            ValueError: If week is invalid.
        """
        if week <= self.current_week:
            raise ValueError(
                f"Cannot advance backwards. Current: {self.current_week}, requested: {week}"
            )
        if week > 18:
            raise ValueError(f"Invalid week: {week}. Max is 18.")

        self.current_week = week
        self.status = "ready"
        self.updated_at = datetime.utcnow().isoformat()

    def get_included_weeks(self) -> list[int]:
        """Get list of weeks to include in training.

        Returns:
            List of weeks 1 through current_week, or empty if pre-season.
        """
        if self.current_week == 0:
            return []
        return list(range(1, self.current_week + 1))


def load_state(path: Path | None = None) -> SimulationState | None:
    """Load simulation state from file.

    Args:
        path: Path to state file. Defaults to STATE_FILE.

    Returns:
        SimulationState if file exists, None otherwise.
    """
    path = path or STATE_FILE

    if not path.exists():
        logger.info(f"No state file found at {path}")
        return None

    with open(path) as f:
        data = json.load(f)

    logger.info(f"Loaded simulation state from {path}")
    return SimulationState.from_dict(data)


def save_state(state: SimulationState, path: Path | None = None) -> Path:
    """Save simulation state to file.

    Args:
        state: SimulationState to save.
        path: Path to state file. Defaults to STATE_FILE.

    Returns:
        Path where state was saved.
    """
    path = path or STATE_FILE

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp
    state.updated_at = datetime.utcnow().isoformat()

    with open(path, "w") as f:
        json.dump(state.to_dict(), f, indent=2)

    logger.info(f"Saved simulation state to {path}")
    return path


def initialize_state(
    target_season: int = 2025,
    training_seasons: list[int] | None = None,
    name: str | None = None,
) -> SimulationState:
    """Create a new simulation state.

    Args:
        target_season: Season to simulate (default: 2025).
        training_seasons: Base seasons for training (default: [2022, 2023, 2024]).
        name: Simulation name (default: "<target_season> Season Simulation").

    Returns:
        New SimulationState at week 0 (pre-season).
    """
    if training_seasons is None:
        training_seasons = [2022, 2023, 2024]

    if name is None:
        name = f"{target_season} Season Simulation"

    state = SimulationState(
        name=name,
        target_season=target_season,
        training_seasons=training_seasons,
        current_week=0,
        status="ready",
    )

    logger.info(
        f"Initialized simulation: {name}, target={target_season}, "
        f"training={training_seasons}"
    )

    return state


def reset_state(state: SimulationState) -> SimulationState:
    """Reset simulation to pre-season state.

    Args:
        state: Current simulation state.

    Returns:
        Reset SimulationState at week 0.
    """
    state.current_week = 0
    state.status = "ready"
    state.last_trained_at = None
    state.updated_at = datetime.utcnow().isoformat()

    logger.info(f"Reset simulation to week 0")
    return state
