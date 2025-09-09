"""
Enums for BDD Property Tracker models
"""
from enum import Enum


class PropertyStatus(str, Enum):
    PROPERTY_SOURCING = "PROPERTY_SOURCING"
    PROPERTY_STUDY = "PROPERTY_STUDY"
    PBY_PREPARATION = "PBY_PREPARATION"
    COUNCIL_APPROVAL = "COUNCIL_APPROVAL"
    NEGOTIATION = "NEGOTIATION"
    DUE_DILIGENCE = "DUE_DILIGENCE"
    CONTRACT_SIGNING = "CONTRACT_SIGNING"
    TAKEOVER = "TAKEOVER"


class PropertyType(str, Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    AGRICULTURAL = "AGRICULTURAL"
    MIXED_USE = "MIXED_USE"


class UserRole(str, Enum):
    # Admin Portal - BDD Employee Management (Separate Portal)
    ADMIN = "ADMIN"                    # System admin - manages users and system
    
    # Main Property Management Portal - Property Users
    BDD_USER = "BDD_USER"              # BDD internal user - full property access
    AGENT = "AGENT"                    # Property agent - can submit properties
    BROKER = "BROKER"                  # Property broker - can review and approve