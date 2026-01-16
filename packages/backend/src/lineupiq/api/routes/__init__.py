"""
API routes for LineupIQ.
"""

from lineupiq.api.routes.predictions import router
from lineupiq.api.routes.roster import router as roster_router
from lineupiq.api.routes.validation import router as validation_router

__all__ = ["router", "validation_router", "roster_router"]
