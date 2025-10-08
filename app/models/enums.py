"""
Enums for BDD Property Tracker models
"""
from enum import Enum


class PropertyStatus(str, Enum):
    PROPERTY_SOURCING = "PROPERTY_SOURCING"
    PROPERTY_SCREENING_FUNG_SHUI = "PROPERTY_SCREENING_FUNG_SHUI"
    PBY_STUDY = "PBY_STUDY"
    EXECOM = "EXECOM"
    BOARD_APPROVAL = "BOARD_APPROVAL"
    DUE_DILIGENCE = "DUE_DILIGENCE"
    NEGOTIATION = "NEGOTIATION"
    COL_DOAS_SIGNING = "COL_DOAS_SIGNING"


class PropertyType(str, Enum):
    LAND_ONLY = "LAND_ONLY"
    LAND_AND_BUILDING = "LAND_AND_BUILDING"
    BUILDING_ONLY = "BUILDING_ONLY"
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    AGRICULTURAL = "AGRICULTURAL"
    MIXED_USE = "MIXED_USE"
    HOTEL = "HOTEL"


class UserRole(str, Enum):
    # Admin Portal - BDD Employee Management (Separate Portal)
    ADMIN = "ADMIN"                    # System admin - manages users and system
    
    # Main Property Management Portal - Property Users
    BDD_USER = "BDD_USER"              # BDD internal user - full property access
    AGENT = "AGENT"                    # Property agent - can submit properties
    BROKER = "BROKER"                  # Property broker - can review and approve


class TransactionMode(str, Enum):
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    FACE_TO_FACE = "FACE_TO_FACE"
    VIDEO_CALL = "VIDEO_CALL"
    LETTER = "LETTER"


class AccountStatus(str, Enum):
    PENDING = "PENDING"        # Account created but awaiting admin approval
    APPROVED = "APPROVED"      # Account approved by admin, user can login
    REJECTED = "REJECTED"      # Account rejected by admin


class TransactionStatus(str, Enum):
    S = "S"  # Sale
    L = "L"  # Lease
    SL = "SL"  # Sale Leaseback  
    JV = "JV"  # Joint Venture


class ZoningClassification(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    AGRICULTURAL = "Agricultural"
    AGRICULTURAL_BEACH_FRONT = "Agricultural - Beach Front"
    INDUSTRIAL = "Industrial"