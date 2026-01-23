"""
Upload 2025 validation predictions to Convex.

Usage:
  uv run python scripts/upload_validation_to_convex.py --file validation_2025_predictions.json
  uv run python scripts/upload_validation_to_convex.py --batch-size 50
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_prediction(pred: dict) -> dict:
    """Transform snake_case JSON to camelCase for Convex."""
    return {
        "playerId": pred["player_id"],
        "playerName": pred["player_name"],
        "position": pred["position"],
        "season": pred["season"],
        "week": pred["week"],
        "target": pred["target"],
        "predictedValue": pred["predicted_value"],
        "actualValue": pred["actual_value"],
    }


def upload_to_convex(predictions: list[dict], convex_url: str, batch_size: int = 100):
    """Upload predictions to Convex in batches."""
    total = len(predictions)
    uploaded = 0

    for i in range(0, total, batch_size):
        batch_raw = predictions[i : i + batch_size]
        # Transform snake_case to camelCase
        batch = [transform_prediction(pred) for pred in batch_raw]

        # Call Convex mutation
        response = requests.post(
            f"{convex_url}/api/mutation",
            json={
                "path": "validationPredictions:upsertValidationPredictions",
                "args": {"predictions": batch},
            },
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            logger.error(f"Failed to upload batch {i//batch_size + 1}: {response.text}")
            continue

        result = response.json()
        uploaded += len(batch)
        logger.info(
            f"Batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}: "
            f"Uploaded {uploaded}/{total} predictions "
            f"(inserted: {result.get('inserted', 0)}, updated: {result.get('updated', 0)})"
        )

    return uploaded


def main():
    parser = argparse.ArgumentParser(description="Upload 2025 validation predictions to Convex")
    parser.add_argument(
        "--file",
        type=str,
        default="validation_2025_predictions.json",
        help="Path to validation predictions JSON file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of predictions per batch (default: 100)",
    )
    args = parser.parse_args()

    # Load predictions from JSON
    predictions_file = Path(args.file)
    if not predictions_file.exists():
        logger.error(f"Predictions file not found: {predictions_file}")
        sys.exit(1)

    with open(predictions_file) as f:
        predictions = json.load(f)

    logger.info(f"Loaded {len(predictions)} predictions from {predictions_file}")

    # Get Convex URL from environment (should be set in frontend .env.local)
    # Read from packages/frontend/.env.local
    env_file = Path(__file__).parent.parent.parent / "frontend" / ".env.local"
    if not env_file.exists():
        logger.error("Frontend .env.local not found. Run `pnpm convex dev` first.")
        sys.exit(1)

    convex_url = None
    with open(env_file) as f:
        for line in f:
            if line.startswith("NEXT_PUBLIC_CONVEX_URL="):
                convex_url = line.split("=", 1)[1].strip()
                break

    if not convex_url:
        logger.error("NEXT_PUBLIC_CONVEX_URL not found in .env.local")
        sys.exit(1)

    logger.info(f"Uploading to Convex: {convex_url}")

    # Upload to Convex
    uploaded = upload_to_convex(predictions, convex_url, args.batch_size)

    logger.info(f"Upload complete: {uploaded}/{len(predictions)} predictions uploaded")


if __name__ == "__main__":
    main()
