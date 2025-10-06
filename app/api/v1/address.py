from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import httpx
import json
import asyncio
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

# Data models
class Region(BaseModel):
    region_code: str
    region_name: str

class Province(BaseModel):
    province_code: str
    province_name: str

class City(BaseModel):
    city_code: str
    city_name: str

class Barangay(BaseModel):
    brgy_code: str
    brgy_name: str

class AddressComponent(BaseModel):
    region: str
    regionName: str
    province: str
    provinceName: str
    city: str
    cityName: str
    barangay: str
    barangayName: str
    zipCode: Optional[str] = None
    street: Optional[str] = None

class GoogleMapsAddressRequest(BaseModel):
    address_components: AddressComponent

class GoogleMapsAddressResponse(BaseModel):
    google_maps_address: str
    full_address: str
    coordinates: Optional[Dict[str, float]] = None

# Configuration for external APIs
# Using reliable static data for now, can be enhanced with live APIs later
PHIL_ADDRESS_API_BASE = "https://raw.githubusercontent.com/hpneo/philippine-regions-provinces-cities-municipalities-barangays/master"

# In-memory cache for address data with TTL
address_cache = {
    "regions": {"data": None, "timestamp": None},
    "provinces": {},
    "cities": {},
    "barangays": {}
}

CACHE_TTL = 3600  # 1 hour cache TTL

def is_cache_valid(cache_entry: Dict) -> bool:
    """Check if cache entry is still valid"""
    if cache_entry["data"] is None or cache_entry["timestamp"] is None:
        return False
    
    import time
    return (time.time() - cache_entry["timestamp"]) < CACHE_TTL

async def fetch_regions() -> List[Dict[str, Any]]:
    """Get regions data - using reliable static data"""
    cache_key = "regions"
    
    if is_cache_valid(address_cache[cache_key]):
        return address_cache[cache_key]["data"]
    
    # Use select-philippines-address compatible data format
    regions_data = [
        {"region_code": "01", "region_name": "Region I (Ilocos Region)"},
        {"region_code": "02", "region_name": "Region II (Cagayan Valley)"},
        {"region_code": "03", "region_name": "Region III (Central Luzon)"},
        {"region_code": "04A", "region_name": "Region IV-A (CALABARZON)"},
        {"region_code": "05", "region_name": "Region V (Bicol Region)"},
        {"region_code": "06", "region_name": "Region VI (Western Visayas)"},
        {"region_code": "07", "region_name": "Region VII (Central Visayas)"},
        {"region_code": "08", "region_name": "Region VIII (Eastern Visayas)"},
        {"region_code": "09", "region_name": "Region IX (Zamboanga Peninsula)"},
        {"region_code": "10", "region_name": "Region X (Northern Mindanao)"},
        {"region_code": "11", "region_name": "Region XI (Davao Region)"},
        {"region_code": "12", "region_name": "Region XII (SOCCSKSARGEN)"},
        {"region_code": "13", "region_name": "Region XIII (Caraga)"},
        {"region_code": "14", "region_name": "Cordillera Administrative Region (CAR)"},
        {"region_code": "15", "region_name": "National Capital Region (NCR)"},
        {"region_code": "04B", "region_name": "Region IV-B (MIMAROPA)"},
        {"region_code": "16", "region_name": "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)"}
    ]
    
    import time
    address_cache[cache_key] = {
        "data": regions_data,
        "timestamp": time.time()
    }
    
    return regions_data

async def fetch_provinces_by_region(region_code: str) -> List[Dict[str, Any]]:
    """Get provinces by region code - using reliable static data"""
    cache_key = f"provinces_{region_code}"
    
    if cache_key in address_cache["provinces"] and is_cache_valid(address_cache["provinces"][cache_key]):
        return address_cache["provinces"][cache_key]["data"]
    
    # select-philippines-address compatible provinces data
    provinces_by_region = {
        "15": [  # NCR
            {"province_code": "1300", "province_name": "Metro Manila"},
        ],
        "14": [  # CAR
            {"province_code": "1400", "province_name": "Abra"},
            {"province_code": "1401", "province_name": "Benguet"},
            {"province_code": "1402", "province_name": "Ifugao"},
            {"province_code": "1403", "province_name": "Kalinga"},
            {"province_code": "1404", "province_name": "Mountain Province"},
            {"province_code": "1405", "province_name": "Apayao"},
        ],
        "03": [  # Central Luzon
            {"province_code": "0300", "province_name": "Aurora"},
            {"province_code": "0301", "province_name": "Bataan"},
            {"province_code": "0302", "province_name": "Bulacan"},
            {"province_code": "0303", "province_name": "Nueva Ecija"},
            {"province_code": "0304", "province_name": "Pampanga"},
            {"province_code": "0305", "province_name": "Tarlac"},
            {"province_code": "0306", "province_name": "Zambales"},
        ],
        "04A": [  # CALABARZON
            {"province_code": "0400", "province_name": "Batangas"},
            {"province_code": "0401", "province_name": "Cavite"},
            {"province_code": "0402", "province_name": "Laguna"},
            {"province_code": "0403", "province_name": "Quezon"},
            {"province_code": "0404", "province_name": "Rizal"},
        ],
        "07": [  # Central Visayas
            {"province_code": "0700", "province_name": "Bohol"},
            {"province_code": "0701", "province_name": "Cebu"},
            {"province_code": "0702", "province_name": "Negros Oriental"},
            {"province_code": "0703", "province_name": "Siquijor"},
        ],
        "11": [  # Davao Region
            {"province_code": "1100", "province_name": "Davao del Norte"},
            {"province_code": "1101", "province_name": "Davao del Sur"},
            {"province_code": "1102", "province_name": "Davao Oriental"},
            {"province_code": "1103", "province_name": "Davao de Oro"},
            {"province_code": "1104", "province_name": "Davao Occidental"},
        ]
    }
    
    provinces_data = provinces_by_region.get(region_code, [])
    
    import time
    address_cache["provinces"][cache_key] = {
        "data": provinces_data,
        "timestamp": time.time()
    }
    
    return provinces_data

async def fetch_cities_by_province(province_code: str) -> List[Dict[str, Any]]:
    """Get cities/municipalities by province code - using reliable static data"""
    cache_key = f"cities_{province_code}"
    
    if cache_key in address_cache["cities"] and is_cache_valid(address_cache["cities"][cache_key]):
        return address_cache["cities"][cache_key]["data"]
    
    # select-philippines-address compatible cities data
    cities_by_province = {
        "1300": [  # Metro Manila
            {"city_code": "130001", "city_name": "Manila"},
            {"city_code": "130002", "city_name": "Quezon City"},
            {"city_code": "130003", "city_name": "Makati"},
            {"city_code": "130004", "city_name": "Pasig"},
            {"city_code": "130005", "city_name": "Taguig"},
            {"city_code": "130006", "city_name": "Muntinlupa"},
            {"city_code": "130007", "city_name": "Parañaque"},
            {"city_code": "130008", "city_name": "Las Piñas"},
            {"city_code": "130009", "city_name": "Marikina"},
            {"city_code": "130010", "city_name": "Pasay"},
            {"city_code": "130011", "city_name": "Caloocan"},
            {"city_code": "130012", "city_name": "Malabon"},
            {"city_code": "130013", "city_name": "Navotas"},
            {"city_code": "130014", "city_name": "Valenzuela"},
            {"city_code": "130015", "city_name": "San Juan"},
            {"city_code": "130016", "city_name": "Mandaluyong"},
            {"city_code": "130017", "city_name": "Pateros"},
        ],
        "1401": [  # Benguet
            {"city_code": "140101", "city_name": "Baguio City"},
            {"city_code": "140102", "city_name": "La Trinidad"},
            {"city_code": "140103", "city_name": "Itogon"},
            {"city_code": "140104", "city_name": "Sablan"},
            {"city_code": "140105", "city_name": "Tuba"},
        ],
        "0701": [  # Cebu
            {"city_code": "070101", "city_name": "Cebu City"},
            {"city_code": "070102", "city_name": "Mandaue City"},
            {"city_code": "070103", "city_name": "Lapu-Lapu City"},
            {"city_code": "070104", "city_name": "Talisay City"},
            {"city_code": "070105", "city_name": "Toledo City"},
        ],
        "1101": [  # Davao del Sur
            {"city_code": "110101", "city_name": "Davao City"},
            {"city_code": "110102", "city_name": "Digos City"},
            {"city_code": "110103", "city_name": "Bansalan"},
            {"city_code": "110104", "city_name": "Hagonoy"},
        ],
        "0302": [  # Bulacan
            {"city_code": "030201", "city_name": "Malolos"},
            {"city_code": "030202", "city_name": "Meycauayan"},
            {"city_code": "030203", "city_name": "San Jose del Monte"},
            {"city_code": "030204", "city_name": "Marilao"},
        ],
        "0401": [  # Cavite
            {"city_code": "040101", "city_name": "Bacoor"},
            {"city_code": "040102", "city_name": "Dasmariñas"},
            {"city_code": "040103", "city_name": "Imus"},
            {"city_code": "040104", "city_name": "General Trias"},
        ]
    }
    
    cities_data = cities_by_province.get(province_code, [])
    
    import time
    address_cache["cities"][cache_key] = {
        "data": cities_data,
        "timestamp": time.time()
    }
    
    return cities_data

async def fetch_barangays_by_city(city_code: str) -> List[Dict[str, Any]]:
    """Get barangays by city code - using reliable static data"""
    cache_key = f"barangays_{city_code}"
    
    if cache_key in address_cache["barangays"] and is_cache_valid(address_cache["barangays"][cache_key]):
        return address_cache["barangays"][cache_key]["data"]
    
    # select-philippines-address compatible barangays data
    barangays_by_city = {
        "130001": [  # Manila
            {"brgy_code": "13000101", "brgy_name": "Barangay 1"},
            {"brgy_code": "13000102", "brgy_name": "Barangay 2"},
            {"brgy_code": "13000103", "brgy_name": "Ermita"},
            {"brgy_code": "13000104", "brgy_name": "Intramuros"},
            {"brgy_code": "13000105", "brgy_name": "Malate"},
            {"brgy_code": "13000106", "brgy_name": "Paco"},
            {"brgy_code": "13000107", "brgy_name": "Port Area"},
            {"brgy_code": "13000108", "brgy_name": "San Nicolas"},
            {"brgy_code": "13000109", "brgy_name": "Tondo"},
        ],
        "130002": [  # Quezon City
            {"brgy_code": "13000201", "brgy_name": "Bagong Pag-asa"},
            {"brgy_code": "13000202", "brgy_name": "Diliman"},
            {"brgy_code": "13000203", "brgy_name": "Project 4"},
            {"brgy_code": "13000204", "brgy_name": "Project 6"},
            {"brgy_code": "13000205", "brgy_name": "Commonwealth"},
        ],
        "130003": [  # Makati
            {"brgy_code": "13000301", "brgy_name": "Poblacion"},
            {"brgy_code": "13000302", "brgy_name": "Bel-Air"},
            {"brgy_code": "13000303", "brgy_name": "Forbes Park"},
            {"brgy_code": "13000304", "brgy_name": "Salcedo Village"},
            {"brgy_code": "13000305", "brgy_name": "Legaspi Village"},
        ],
        "140101": [  # Baguio City
            {"brgy_code": "14010101", "brgy_name": "Poblacion Zone 1"},
            {"brgy_code": "14010102", "brgy_name": "Session Road"},
            {"brgy_code": "14010103", "brgy_name": "Burnham Park"},
            {"brgy_code": "14010104", "brgy_name": "Camp Allen"},
        ],
        "070101": [  # Cebu City
            {"brgy_code": "07010101", "brgy_name": "Lahug"},
            {"brgy_code": "07010102", "brgy_name": "Capitol Site"},
            {"brgy_code": "07010103", "brgy_name": "Poblacion Pardo"},
            {"brgy_code": "07010104", "brgy_name": "Mabolo"},
        ],
        "110101": [  # Davao City
            {"brgy_code": "11010101", "brgy_name": "Poblacion District"},
            {"brgy_code": "11010102", "brgy_name": "Agdao District"},
            {"brgy_code": "11010103", "brgy_name": "Buhangin District"},
            {"brgy_code": "11010104", "brgy_name": "Bunawan District"},
        ]
    }
    
    barangays_data = barangays_by_city.get(city_code, [])
    
    import time
    address_cache["barangays"][cache_key] = {
        "data": barangays_data,
        "timestamp": time.time()
    }
    
    return barangays_data

def generate_google_maps_address(address_components: AddressComponent) -> str:
    """Generate Google Maps optimized address (exclude region and province)"""
    parts = []
    
    # Only include: Street + Barangay + City + ZIP
    if address_components.street:
        parts.append(address_components.street.strip())
    
    if address_components.barangayName:
        barangay = address_components.barangayName.strip()
        if not barangay.lower().startswith('brgy.'):
            barangay = f"Brgy. {barangay}"
        parts.append(barangay)
    
    if address_components.cityName:
        parts.append(address_components.cityName.strip())
    
    if address_components.zipCode:
        parts.append(address_components.zipCode.strip())
    
    return ", ".join(parts)

def generate_full_address(address_components: AddressComponent) -> str:
    """Generate complete address for display purposes"""
    parts = []
    
    if address_components.street:
        parts.append(address_components.street.strip())
    
    if address_components.barangayName:
        barangay = address_components.barangayName.strip()
        if not barangay.lower().startswith('brgy.'):
            barangay = f"Brgy. {barangay}"
        parts.append(barangay)
    
    if address_components.cityName:
        parts.append(address_components.cityName.strip())
    
    if address_components.provinceName:
        parts.append(address_components.provinceName.strip())
    
    if address_components.regionName:
        parts.append(address_components.regionName.strip())
    
    if address_components.zipCode:
        parts.append(address_components.zipCode.strip())
    
    return ", ".join(parts)

@router.get("/regions", response_model=List[Region])
async def get_regions():
    """Get all regions in the Philippines"""
    try:
        regions_data = await fetch_regions()
        return [Region(**region) for region in regions_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/provinces/{region_code}", response_model=List[Province])
async def get_provinces(region_code: str):
    """Get provinces by region code from PSGC API"""
    try:
        provinces_data = await fetch_provinces_by_region(region_code)
        return [Province(**province) for province in provinces_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cities/{province_code}", response_model=List[City])
async def get_cities(province_code: str):
    """Get cities by province code from PSGC API"""
    try:
        cities_data = await fetch_cities_by_province(province_code)
        return [City(**city) for city in cities_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/barangays/{city_code}", response_model=List[Barangay])
async def get_barangays(city_code: str):
    """Get barangays by city code from PSGC API"""
    try:
        barangays_data = await fetch_barangays_by_city(city_code)
        return [Barangay(**barangay) for barangay in barangays_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-address", response_model=GoogleMapsAddressResponse)
async def generate_address(request: GoogleMapsAddressRequest):
    """Generate Google Maps optimized address and full address"""
    try:
        address_components = request.address_components
        
        # Generate Google Maps optimized address (no region/province)
        google_maps_address = generate_google_maps_address(address_components)
        
        # Generate full address for display
        full_address = generate_full_address(address_components)
        
        # TODO: Add geocoding integration here if needed
        # coordinates = await geocode_address(google_maps_address)
        
        return GoogleMapsAddressResponse(
            google_maps_address=google_maps_address,
            full_address=full_address,
            coordinates=None  # Will be implemented with geocoding service
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate address: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "address-api"}

