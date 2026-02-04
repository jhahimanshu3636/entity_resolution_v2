"""
Utility Functions for Entity Resolution System
==============================================

Common utility functions for string processing, validation, and helpers.

Author: Entity Resolution System
"""

import re
import unicodedata
from typing import List, Set, Optional, Tuple
import phonenumbers
from phonenumbers import NumberParseException


# ============================================================================
# STRING NORMALIZATION
# ============================================================================

def normalize_string(text: str, lowercase: bool = True, remove_special: bool = True) -> str:
    """
    Normalize string for comparison
    
    Args:
        text: Input string
        lowercase: Convert to lowercase
        remove_special: Remove special characters
        
    Returns:
        Normalized string
    """
    if not text:
        return ""
    
    # Unicode normalization (NFD = decompose, remove accents)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Lowercase
    if lowercase:
        text = text.lower()
    
    # Remove special characters
    if remove_special:
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def tokenize(text: str, min_length: int = 2) -> List[str]:
    """
    Tokenize text into words
    
    Args:
        text: Input text
        min_length: Minimum token length
        
    Returns:
        List of tokens
    """
    normalized = normalize_string(text)
    tokens = [t for t in normalized.split() if len(t) >= min_length]
    return tokens


def generate_ngrams(text: str, n: int = 3) -> Set[str]:
    """
    Generate character n-grams from text
    
    Args:
        text: Input text
        n: N-gram size
        
    Returns:
        Set of n-grams
    """
    normalized = normalize_string(text, remove_special=False)
    # Add padding
    padded = f"__{normalized}__"
    ngrams = {padded[i:i+n] for i in range(len(padded) - n + 1)}
    return ngrams


# ============================================================================
# PHONE NUMBER NORMALIZATION
# ============================================================================

def normalize_phone(phone: str, region: str = "US") -> Optional[str]:
    """
    Normalize phone number to E.164 format
    
    Args:
        phone: Phone number string
        region: ISO country code (default: US)
        
    Returns:
        Normalized phone number or None if invalid
    """
    try:
        parsed = phonenumbers.parse(phone, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
    except NumberParseException:
        pass
    
    return None


# ============================================================================
# EMAIL NORMALIZATION
# ============================================================================

def normalize_email(email: str) -> Optional[str]:
    """
    Normalize email address
    
    Args:
        email: Email address
        
    Returns:
        Normalized email or None if invalid
    """
    if not email or '@' not in email:
        return None
    
    try:
        local, domain = email.lower().strip().split('@', 1)
        
        # Remove dots from Gmail addresses (user.name@gmail.com == username@gmail.com)
        if domain in ['gmail.com', 'googlemail.com']:
            local = local.replace('.', '')
            # Remove everything after + (user+tag@gmail.com == user@gmail.com)
            if '+' in local:
                local = local.split('+')[0]
        
        return f"{local}@{domain}"
    except Exception:
        return None


# ============================================================================
# ADDRESS NORMALIZATION
# ============================================================================

# Common address abbreviations
ADDRESS_ABBREVIATIONS = {
    'street': 'st',
    'avenue': 'ave',
    'boulevard': 'blvd',
    'drive': 'dr',
    'road': 'rd',
    'lane': 'ln',
    'court': 'ct',
    'circle': 'cir',
    'place': 'pl',
    'apartment': 'apt',
    'suite': 'ste',
    'floor': 'fl',
    'building': 'bldg',
    'north': 'n',
    'south': 's',
    'east': 'e',
    'west': 'w',
    'northeast': 'ne',
    'northwest': 'nw',
    'southeast': 'se',
    'southwest': 'sw'
}


def normalize_address(address: str) -> str:
    """
    Normalize address for comparison
    
    Args:
        address: Address string
        
    Returns:
        Normalized address
    """
    if not address:
        return ""
    
    # Basic normalization
    normalized = normalize_string(address)
    
    # Expand common abbreviations
    tokens = normalized.split()
    expanded = []
    
    for token in tokens:
        # Replace abbreviations with standard forms
        replaced = False
        for full, abbr in ADDRESS_ABBREVIATIONS.items():
            if token == abbr or token == full:
                expanded.append(abbr)
                replaced = True
                break
        if not replaced:
            expanded.append(token)
    
    return ' '.join(expanded)


# ============================================================================
# IP ADDRESS UTILITIES
# ============================================================================

def get_ip_subnet(ip_address: str, prefix_length: int = 24) -> Optional[str]:
    """
    Get IP subnet for comparison
    
    Args:
        ip_address: IP address string
        prefix_length: Subnet prefix length (default: /24)
        
    Returns:
        Subnet string or None if invalid
    """
    try:
        import ipaddress
        ip = ipaddress.ip_address(ip_address)
        network = ipaddress.ip_network(f"{ip}/{prefix_length}", strict=False)
        return str(network)
    except Exception:
        return None


def ip_distance(ip1: str, ip2: str) -> float:
    """
    Calculate distance between two IP addresses
    
    Args:
        ip1: First IP address
        ip2: Second IP address
        
    Returns:
        Distance score (0 = same IP, 1 = different subnet)
    """
    try:
        import ipaddress
        addr1 = ipaddress.ip_address(ip1)
        addr2 = ipaddress.ip_address(ip2)
        
        if addr1 == addr2:
            return 0.0
        
        # Check if in same /24 subnet
        net1 = ipaddress.ip_network(f"{addr1}/24", strict=False)
        net2 = ipaddress.ip_network(f"{addr2}/24", strict=False)
        
        if net1 == net2:
            return 0.2  # Same subnet
        
        # Check if in same /16 subnet
        net1_16 = ipaddress.ip_network(f"{addr1}/16", strict=False)
        net2_16 = ipaddress.ip_network(f"{addr2}/16", strict=False)
        
        if net1_16 == net2_16:
            return 0.5  # Same /16
        
        return 1.0  # Different networks
    except Exception:
        return 1.0


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Check if email is valid format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str, region: str = "US") -> bool:
    """Check if phone number is valid"""
    return normalize_phone(phone, region) is not None


# ============================================================================
# DEVICE FINGERPRINT UTILITIES
# ============================================================================

def extract_device_features(device_fingerprint: str) -> dict:
    """
    Extract features from device fingerprint
    
    Args:
        device_fingerprint: Device fingerprint string
        
    Returns:
        Dictionary of device features
    """
    # This is a placeholder - in production, device fingerprints
    # would be more complex (Canvas fingerprinting, WebGL, etc.)
    return {
        'fingerprint': device_fingerprint,
        'hash': hash(device_fingerprint),
        'length': len(device_fingerprint)
    }


# ============================================================================
# DISTANCE CALCULATIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two geographic coordinates in kilometers
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    import math
    
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


# ============================================================================
# MISC UTILITIES
# ============================================================================

def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address"""
    try:
        return email.split('@')[1].lower()
    except Exception:
        return None


def is_round_amount(amount: float, threshold: float = 0.01) -> bool:
    """Check if transaction amount is round (ending in .00)"""
    return abs(amount - round(amount)) < threshold


def get_time_of_day_category(hour: int) -> str:
    """Categorize hour of day"""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"
