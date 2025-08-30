from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import crud, models, schemas, bgeigie_parser
from ..security import get_db, get_current_active_user, get_current_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_model=List[schemas.BGeigieImport])
def read_bgeigie_imports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    imports = crud.get_bgeigie_imports_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return imports


@router.get("/{import_id}/detail", response_class=HTMLResponse)
async def get_import_detail(
    request: Request,
    import_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Display detailed view with map for a bGeigie import"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id,
        models.BGeigieImport.user_id == current_user.id
    ).first()
    
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    return templates.TemplateResponse("bgeigie_import_detail.html", {
        "request": request,
        "import": db_import
    })


@router.get("/{import_id}/measurements")
async def get_import_measurements(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get measurement data for map visualization"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id,
        models.BGeigieImport.user_id == current_user.id
    ).first()
    
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Get measurements from bgeigie_logs
    measurements = db.query(models.BGeigieLog).filter(
        models.BGeigieLog.bgeigie_import_id == import_id
    ).all()
    
    measurement_data = []
    for m in measurements:
        # Convert NMEA coordinates to decimal degrees
        lat = nmea_to_decimal(m.latitude_nmea, m.north_south_indicator)
        lng = nmea_to_decimal(m.longitude_nmea, m.east_west_indicator)
        
        measurement_data.append({
            "id": m.id,
            "cpm": m.cpm,
            "latitude": lat,
            "longitude": lng,
            "captured_at": m.captured_at.isoformat(),
            "gps_fix_indicator": m.gps_fix_indicator,
            "altitude": m.altitude
        })
    
    return {
        "measurements": measurement_data,
        "total_count": len(measurement_data),
        "import_id": import_id
    }


@router.put("/{import_id}/metadata")
async def update_import_metadata(
    import_id: int,
    metadata: schemas.BGeigieImportMetadata,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update metadata for a bGeigie import"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id,
        models.BGeigieImport.user_id == current_user.id
    ).first()
    
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    if db_import.status != "processed":
        raise HTTPException(status_code=400, detail="Import must be processed before adding metadata")
    
    # Update metadata fields
    for field, value in metadata.dict(exclude_unset=True).items():
        setattr(db_import, field, value)
    
    # Mark as submitted for approval
    db_import.status = "submitted"
    
    db.commit()
    db.refresh(db_import)
    
    return {"message": "Metadata updated successfully", "import": db_import}


def nmea_to_decimal(nmea_coord: float, direction: str) -> float:
    """Convert NMEA coordinate to decimal degrees"""
    if not nmea_coord:
        return 0.0
    
    # NMEA format: DDMM.MMMM
    degrees = int(nmea_coord / 100)
    minutes = nmea_coord % 100
    decimal = degrees + (minutes / 60)
    
    if direction in ['S', 'W']:
        decimal *= -1
    
    return decimal

@router.post("/", response_model=schemas.BGeigieImport)
async def create_bgeigie_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    if not file.filename.lower().endswith('.log'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .log files are accepted.")

    file_content = await file.read()
    await file.close()

    if not file_content:
        raise HTTPException(status_code=400, detail="File is empty.")

    # Create the import record first
    bgeigie_import_create = schemas.BGeigieImportCreate(source=file.filename)
    db_bgeigie_import = crud.create_bgeigie_import(
        db=db, 
        bgeigie_import=bgeigie_import_create, 
        user_id=current_user.id, 
        file_content=file_content
    )

    # Parse the file and create measurements
    try:
        decoded_content = file_content.decode('utf-8')
        measurements_data = bgeigie_parser.parse_bgeigie_log(decoded_content)
        
        # Filter data to match the Measurement model
        filtered_measurements = [
            {
                'cpm': m['cpm'],
                'latitude': m['latitude'],
                'longitude': m['longitude'],
                'captured_at': m['captured_at'],
            }
            for m in measurements_data
        ]

        if filtered_measurements:
            crud.create_measurements(db=db, measurements=filtered_measurements, bgeigie_import_id=db_bgeigie_import.id)

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Only UTF-8 is supported.")
    except Exception as e:
        # Here you might want to delete the bgeigie_import record if parsing fails
        raise HTTPException(status_code=500, detail=f"Failed to parse and process file: {e}")

    return db_bgeigie_import

@router.patch("/{id}/submit")
def submit_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "submitted", current_user.id)
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    return db_import

@router.patch("/{id}/approve")
def approve_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "approved")
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    return db_import

@router.patch("/{id}/reject")
def reject_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "rejected")
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    return db_import
