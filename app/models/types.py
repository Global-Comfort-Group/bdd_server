"""
Type definitions for BDD Property Tracker
"""
from typing import Literal

# Zoning Classification - human-readable values stored directly in DB
ZoningClassification = Literal[
    "Residential",
    "Commercial",
    "Agricultural",
    "Agricultural - Beach Front",
    "Industrial"
]

# Helper list for validation and iteration
ZONING_CLASSIFICATIONS = [
    "Residential",
    "Commercial",
    "Agricultural",
    "Agricultural - Beach Front",
    "Industrial"
]

