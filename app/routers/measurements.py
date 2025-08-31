from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from .. import crud, schemas, models
from ..security import get_db, get_current_active_user

router = APIRouter(
    tags=["measurements"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Measurement])
def read_measurements(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    latitude: Optional[float] = Query(None, description="Center latitude for geographic filtering"),
    longitude: Optional[float] = Query(None, description="Center longitude for geographic filtering"),
    distance: Optional[float] = Query(None, description="Distance in kilometers for geographic filtering"),
    captured_after: Optional[str] = Query(None, description="Filter measurements after this date (ISO format)"),
    captured_before: Optional[str] = Query(None, description="Filter measurements before this date (ISO format)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieve measurements with optional geographic and temporal filtering.
    Supports DuckDB spatial queries for efficient geographic searches.
    """
    # Build base query
    query = db.query(models.Measurement)
    
    # Apply geographic filtering using DuckDB spatial functions
    if latitude is not None and longitude is not None and distance is not None:
        # Use DuckDB's spatial extension for distance calculations
        # Convert distance from km to degrees (approximate)
        degree_distance = distance / 111.0  # 1 degree ≈ 111 km
        
        # Use bounding box for efficient filtering
        lat_min = latitude - degree_distance
        lat_max = latitude + degree_distance
        lon_min = longitude - degree_distance
        lon_max = longitude + degree_distance
        
        query = query.filter(
            models.Measurement.latitude.between(lat_min, lat_max),
            models.Measurement.longitude.between(lon_min, lon_max)
        )
        
        # For more precise distance calculation, we can use raw SQL with DuckDB spatial functions
        # This would require the spatial extension to be loaded
        
    # Apply temporal filtering
    if captured_after:
        query = query.filter(models.Measurement.captured_at >= captured_after)
    if captured_before:
        query = query.filter(models.Measurement.captured_at <= captured_before)
    
    # Apply user filtering
    if user_id:
        query = query.join(models.BGeigieImport).filter(models.BGeigieImport.user_id == user_id)
    
    measurements = query.offset(skip).limit(limit).all()
    return measurements

@router.get("/count")
def get_measurements_count(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    distance: Optional[float] = Query(None),
    captured_after: Optional[str] = Query(None),
    captured_before: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get count of measurements with same filtering options as the main endpoint.
    """
    query = db.query(models.Measurement)
    
    # Apply same filters as read_measurements
    if latitude is not None and longitude is not None and distance is not None:
        degree_distance = distance / 111.0
        lat_min = latitude - degree_distance
        lat_max = latitude + degree_distance
        lon_min = longitude - degree_distance
        lon_max = longitude + degree_distance
        
        query = query.filter(
            models.Measurement.latitude.between(lat_min, lat_max),
            models.Measurement.longitude.between(lon_min, lon_max)
        )
    
    if captured_after:
        query = query.filter(models.Measurement.captured_at >= captured_after)
    if captured_before:
        query = query.filter(models.Measurement.captured_at <= captured_before)
    
    if user_id:
        query = query.join(models.BGeigieImport).filter(models.BGeigieImport.user_id == user_id)
    
    count = query.count()
    return {"count": count}

@router.get("/spatial/nearby", response_model=List[schemas.Measurement])
def get_nearby_measurements(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Find measurements within a specific radius using DuckDB spatial capabilities.
    """
    # Use DuckDB's spatial functions for precise distance calculation
    # This is a more accurate approach than simple bounding box
    sql_query = text("""
        SELECT m.id, m.cpm, m.latitude, m.longitude, m.captured_at, m.bgeigie_import_id, m.device_id,
               (6371 * acos(cos(radians(:lat)) * cos(radians(m.latitude)) * 
                cos(radians(m.longitude) - radians(:lon)) + 
                sin(radians(:lat)) * sin(radians(m.latitude)))) AS distance_km
        FROM measurements m
        WHERE (6371 * acos(cos(radians(:lat)) * cos(radians(m.latitude)) * 
               cos(radians(m.longitude) - radians(:lon)) + 
               sin(radians(:lat)) * sin(radians(m.latitude)))) <= :radius
        ORDER BY distance_km
        LIMIT :limit
    """)
    
    result = db.execute(sql_query, {
        'lat': latitude,
        'lon': longitude,
        'radius': radius_km,
        'limit': limit
    })
    
    measurements = []
    for row in result:
        measurements.append(schemas.Measurement(
            id=row.id,
            cpm=row.cpm,
            latitude=row.latitude,
            longitude=row.longitude,
            captured_at=row.captured_at,
            bgeigie_import_id=row.bgeigie_import_id,
            device_id=row.device_id
        ))
    
    return measurements
