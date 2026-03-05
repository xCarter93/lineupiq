#!/usr/bin/env python3
"""
Season simulation CLI for backtesting predictions.

Simulates the target season week-by-week, starting with models trained only on
prior seasons. As weeks "advance," models are retrained with each week's actual
data and predictions are regenerated for remaining weeks.

Usage:
    # Initialize simulation: train 2022-2024 models, generate all 2025 predictions
    uv run python scripts/simulate_season.py init --target-season 2025

    # Advance: incorporate week N actuals, retrain, regenerate predictions
    uv run python scripts/simulate_season.py advance --week 1

    # Status: show current simulation state
    uv run python scripts/simulate_season.py status

    # Reset: reset simulation to week 0
    uv run python scripts/simulate_season.py reset
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import from scripts/
SCRIPTS_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SIMULATION_DIR = BACKEND_DIR / "data" / "simulation"
PREDICTIONS_DIR = SIMULATION_DIR / "predictions"


def cmd_init(args):
    """Initialize a new simulation."""
    from lineupiq.simulation.state import initialize_state, save_state
    from lineupiq.simulation.batch_predict import generate_batch_predictions
    from train_all import train_all_models

    target_season = args.target_season
    training_seasons = list(range(2022, target_season))  # e.g., [2022, 2023, 2024]

    logger.info("=" * 80)
    logger.info(f"INITIALIZING {target_season} SEASON SIMULATION")
    logger.info("=" * 80)
    logger.info(f"Training seasons: {training_seasons}")
    logger.info(f"Target season: {target_season}")

    # Create simulation state
    state = initialize_state(
        target_season=target_season,
        training_seasons=training_seasons,
    )
    state.status = "training"
    save_state(state)

    # Train models on base seasons only (excluding target season)
    logger.info("\nStep 1: Training models on base seasons...")
    n_trials = 10 if args.quick else 30

    results = train_all_models(
        positions=["QB", "RB", "WR", "TE", "K", "DEF"],
        seasons=training_seasons,
        n_trials=n_trials,
    )

    if results is None:
        logger.error("Model training failed")
        state.status = "ready"
        save_state(state)
        return 1

    # Update state with training timestamp
    state.status = "predicting"
    state.last_trained_at = datetime.utcnow().isoformat()
    save_state(state)

    # Generate predictions for all weeks of target season
    logger.info(f"\nStep 2: Generating predictions for all weeks of {target_season}...")
    target_weeks = list(range(1, 19))  # Weeks 1-18
    completed_weeks = []  # No weeks completed yet

    predictions = generate_batch_predictions(
        season=target_season,
        target_weeks=target_weeks,
        completed_weeks=completed_weeks,
        positions=["QB", "RB", "WR", "TE", "K", "DEF"],
        output_dir=PREDICTIONS_DIR,
    )

    # Finalize state
    state.status = "ready"
    state.current_week = 1  # Start at week 1, ready to view week 1 predictions
    save_state(state)

    logger.info("\n" + "=" * 80)
    logger.info("SIMULATION INITIALIZED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Models trained on: {training_seasons}")
    logger.info(f"Predictions generated for weeks 1-18 of {target_season}")
    logger.info(f"Total predictions: {len(predictions)}")
    logger.info(f"\nNext: Run 'simulate_season.py advance --week 1' to advance to week 1")

    return 0


def cmd_advance(args):
    """Advance simulation to incorporate new week's data."""
    from lineupiq.simulation.state import load_state, save_state
    from lineupiq.simulation.batch_predict import generate_batch_predictions
    from train_all import train_all_models

    target_week = args.week

    # Load current state
    state = load_state()
    if state is None:
        logger.error("No simulation found. Run 'init' first.")
        return 1

    if target_week <= state.current_week:
        logger.error(
            f"Cannot advance to week {target_week}. "
            f"Current week is {state.current_week}."
        )
        return 1

    logger.info("=" * 80)
    logger.info(f"ADVANCING TO WEEK {target_week}")
    logger.info("=" * 80)
    logger.info(f"Current week: {state.current_week}")
    logger.info(f"Target season: {state.target_season}")

    # Update state
    state.status = "advancing"
    save_state(state)

    # Determine weeks to include in training
    # If advancing to week N, we have actual data for weeks 1 through N-1
    # We want to predict week N, so week N actuals should NOT be in training
    completed_weeks = list(range(1, target_week))
    logger.info(f"Weeks with actual data: {completed_weeks}")

    # Retrain models with completed weeks
    logger.info("\nStep 1: Retraining models with new data...")
    state.status = "training"
    save_state(state)

    n_trials = 10 if args.quick else 30
    all_seasons = state.training_seasons + [state.target_season]

    results = train_all_models(
        positions=["QB", "RB", "WR", "TE", "K", "DEF"],
        seasons=all_seasons,
        n_trials=n_trials,
        target_season=state.target_season,
        include_weeks=completed_weeks,
    )

    if results is None:
        logger.error("Model retraining failed")
        state.status = "ready"
        save_state(state)
        return 1

    state.last_trained_at = datetime.utcnow().isoformat()

    # Generate predictions for remaining weeks (including the current week we're predicting)
    remaining_weeks = list(range(target_week, 19))

    if remaining_weeks:
        logger.info(f"\nStep 2: Regenerating predictions for weeks {remaining_weeks}...")
        state.status = "predicting"
        save_state(state)

        predictions = generate_batch_predictions(
            season=state.target_season,
            target_weeks=remaining_weeks,
            completed_weeks=completed_weeks,
            positions=["QB", "RB", "WR", "TE", "K", "DEF"],
            output_dir=PREDICTIONS_DIR,
        )
        logger.info(f"Generated {len(predictions)} predictions")

    # Update state to new week
    state.current_week = target_week
    state.status = "ready"
    save_state(state)

    logger.info("\n" + "=" * 80)
    logger.info(f"ADVANCED TO WEEK {target_week}")
    logger.info("=" * 80)
    logger.info(f"Models retrained with weeks 1-{target_week} data")
    if remaining_weeks:
        logger.info(f"Predictions regenerated for weeks {min(remaining_weeks)}-{max(remaining_weeks)}")
    else:
        logger.info("Season complete - no remaining weeks")

    if target_week < 18:
        logger.info(f"\nNext: Run 'simulate_season.py advance --week {target_week + 1}' to continue")

    return 0


def cmd_status(args):
    """Show current simulation status."""
    from lineupiq.simulation.state import load_state
    from lineupiq.simulation.batch_predict import load_predictions

    state = load_state()

    if state is None:
        logger.info("No simulation found. Run 'init' to create one.")
        return 0

    print("\n" + "=" * 60)
    print("SIMULATION STATUS")
    print("=" * 60)
    print(f"Name: {state.name}")
    print(f"Target Season: {state.target_season}")
    print(f"Training Seasons: {state.training_seasons}")
    print(f"Current Week: {state.current_week}")
    print(f"Status: {state.status}")
    print(f"Last Trained: {state.last_trained_at or 'Never'}")
    print(f"Created: {state.created_at}")
    print(f"Updated: {state.updated_at}")
    print("-" * 60)

    # Show prediction counts
    predictions = load_predictions(state.target_season, output_dir=PREDICTIONS_DIR)
    if predictions is not None:
        print(f"\nPredictions on disk:")
        by_week = predictions.group_by("week").count()
        for row in by_week.sort("week").to_dicts():
            print(f"  Week {row['week']}: {row['count']} players")
    else:
        print("\nNo predictions found on disk.")

    print("=" * 60)

    return 0


def cmd_reset(args):
    """Reset simulation to week 0."""
    from lineupiq.simulation.state import load_state, save_state, reset_state

    state = load_state()

    if state is None:
        logger.info("No simulation found.")
        return 0

    if not args.force:
        response = input(f"Reset simulation to week 0? This won't delete predictions. [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return 0

    state = reset_state(state)
    save_state(state)

    logger.info("Simulation reset to week 0")
    return 0


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Season simulation CLI for backtesting predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new season simulation"
    )
    init_parser.add_argument(
        "--target-season",
        type=int,
        default=2025,
        help="Season to simulate (default: 2025)"
    )
    init_parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (10 trials instead of 30)"
    )

    # advance command
    advance_parser = subparsers.add_parser(
        "advance",
        help="Advance simulation to incorporate new week's data"
    )
    advance_parser.add_argument(
        "--week",
        type=int,
        required=True,
        help="Week to advance to (includes this week's actual data)"
    )
    advance_parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (10 trials instead of 30)"
    )

    # status command
    subparsers.add_parser(
        "status",
        help="Show current simulation status"
    )

    # reset command
    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset simulation to week 0"
    )
    reset_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    if args.command is None:
        print("No command specified. Use --help for available commands.")
        return 1

    commands = {
        "init": cmd_init,
        "advance": cmd_advance,
        "status": cmd_status,
        "reset": cmd_reset,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
