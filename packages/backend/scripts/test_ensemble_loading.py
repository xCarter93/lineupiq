"""Quick test to verify ensemble models load correctly via API."""

import logging

from lineupiq.api.models_loader import load_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test that ensemble models load correctly."""
    logger.info("Testing ensemble model loading...")

    models = load_models()

    logger.info(f"\nLoaded {len(models)} total models")

    # Check a few key models
    test_models = [
        "QB_passing_yards",
        "RB_rushing_yards",
        "WR_receiving_yards",
        "TE_receiving_yards",
    ]

    for model_name in test_models:
        if model_name in models:
            model = models[model_name]
            model_type = type(model).__name__
            logger.info(f"✓ {model_name}: {model_type}")

            # Check if it's a VotingRegressor (ensemble)
            if model_type == "VotingRegressor":
                # Get base estimators
                estimators = model.estimators_
                logger.info(f"  └─ Ensemble with {len(estimators)} base models")
            else:
                logger.info(f"  └─ Single model (ensemble not available)")
        else:
            logger.error(f"✗ {model_name}: NOT FOUND")

    logger.info("\n✓ Ensemble loading test complete!")

if __name__ == "__main__":
    main()
