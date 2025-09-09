import re
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation


def validate_philippines_phone(phone: str) -> bool:
    """
    Validate Philippines phone number format.
    
    Accepts formats like:
    - +63 9xx xxx xxxx
    - 09xx xxx xxxx  
    - 9xx xxx xxxx
    """
    if not phone:
        return False
    
    # Remove spaces and dashes
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Philippine phone number patterns
    patterns = [
        r'^\+639\d{9}$',      # +639xxxxxxxxx
        r'^09\d{9}$',         # 09xxxxxxxxx
        r'^9\d{9}$',          # 9xxxxxxxxx
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def validate_title_number(title_number: str) -> bool:
    """
    Validate property title number format.
    Should be alphanumeric and not empty.
    """
    if not title_number:
        return False
    
    # Allow letters, numbers, spaces, and common separators
    pattern = r'^[A-Za-z0-9\s\-\_\/]+$'
    return bool(re.match(pattern, title_number.strip()))


def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validate geographic coordinates.
    
    Args:
        latitude: Latitude value (-90 to 90)
        longitude: Longitude value (-180 to 180)
    
    Returns:
        True if coordinates are valid or both are None
    """
    if latitude is None and longitude is None:
        return True
    
    if latitude is None or longitude is None:
        return False
    
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)


def validate_price(price: Any) -> bool:
    """
    Validate price value.
    Must be a positive number.
    """
    try:
        if isinstance(price, str):
            # Remove currency symbols and commas
            clean_price = re.sub(r'[₱$,\s]', '', price)
            price = Decimal(clean_price)
        elif isinstance(price, (int, float)):
            price = Decimal(str(price))
        elif not isinstance(price, Decimal):
            return False
        
        return price > 0
    except (InvalidOperation, ValueError):
        return False


def validate_lot_area(area: Any) -> bool:
    """
    Validate lot area.
    Must be a positive number.
    """
    try:
        if isinstance(area, str):
            # Remove units and commas
            clean_area = re.sub(r'[sqm²\s,]', '', area.lower())
            area = float(clean_area)
        elif isinstance(area, (int, Decimal)):
            area = float(area)
        elif not isinstance(area, float):
            return False
        
        return area > 0
    except ValueError:
        return False


def validate_postal_code(postal_code: Optional[str]) -> bool:
    """
    Validate Philippines postal code (4 digits).
    """
    if not postal_code:
        return True  # Optional field
    
    return bool(re.match(r'^\d{4}$', postal_code.strip()))


def sanitize_text_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing potential harmful characters.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potential script tags and other harmful content
    sanitized = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    sanitized = re.sub(r'[<>"\']', '', sanitized)  # Remove common injection chars
    sanitized = sanitized.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email_domain(email: str, allowed_domains: Optional[list] = None) -> bool:
    """
    Validate email domain against allowed domains.
    
    Args:
        email: Email address to validate
        allowed_domains: List of allowed domains (if None, all domains allowed)
    
    Returns:
        True if domain is allowed
    """
    if not allowed_domains:
        return True
    
    try:
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in allowed_domains]
    except IndexError:
        return False


class PropertyValidationResult:
    """Result of property validation with detailed errors."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: Dict[str, str] = {}
    
    def add_error(self, field: str, message: str):
        """Add validation error for a field."""
        self.is_valid = False
        self.errors[field] = message


def validate_property_data(data: Dict[str, Any]) -> PropertyValidationResult:
    """
    Comprehensive property data validation.
    
    Args:
        data: Dictionary containing property data
    
    Returns:
        ValidationResult with errors if any
    """
    result = PropertyValidationResult()
    
    # Validate required fields
    required_fields = ['name', 'address', 'lot_area', 'price', 'title_number']
    for field in required_fields:
        if not data.get(field):
            result.add_error(field, f"{field.replace('_', ' ').title()} is required")
    
    # Validate title number format
    if data.get('title_number') and not validate_title_number(data['title_number']):
        result.add_error('title_number', 'Invalid title number format')
    
    # Validate coordinates if provided
    lat = data.get('latitude')
    lon = data.get('longitude')
    if not validate_coordinates(lat, lon):
        result.add_error('coordinates', 'Invalid coordinates provided')
    
    # Validate price
    if data.get('price') and not validate_price(data['price']):
        result.add_error('price', 'Price must be a positive number')
    
    # Validate lot area
    if data.get('lot_area') and not validate_lot_area(data['lot_area']):
        result.add_error('lot_area', 'Lot area must be a positive number')
    
    return result