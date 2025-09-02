from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from .. import crud, models, schemas
from ..security import get_db, get_current_active_user, get_current_admin_user, get_optional_user
from .. import bgeigie_parser
from ..email_service import send_bgeigie_notification_email
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def should_auto_approve(measurements: List[dict], max_cpm: int) -> bool:
    """
    Auto-approval logic based on quality thresholds matching official Safecast criteria.
    """
    # Quality thresholds for auto-approval
    MIN_MEASUREMENTS = 100  # Minimum number of measurements
    MAX_CPM_THRESHOLD = 10000  # Maximum reasonable CPM value
    MIN_GPS_ACCURACY = 0.001  # Minimum GPS coordinate precision
    
    # Check minimum measurement count
    if len(measurements) < MIN_MEASUREMENTS:
        return False
    
    # Check for reasonable CPM values
    if max_cpm > MAX_CPM_THRESHOLD:
        return False
    
    # Check for GPS coordinate validity
    valid_coordinates = 0
    for m in measurements:
        if (abs(m['latitude']) > 0.001 and abs(m['longitude']) > 0.001 and
            -90 <= m['latitude'] <= 90 and -180 <= m['longitude'] <= 180):
            valid_coordinates += 1
    
    # Require at least 90% valid GPS coordinates
    if valid_coordinates / len(measurements) < 0.9:
        return False
    
    return True


@router.get("/")
def read_bgeigie_imports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    # Public access - show all approved imports, or user's own imports if logged in
    if current_user and current_user.role == 'admin':
        # Admins see all imports
        imports = db.query(models.BGeigieImport).join(models.User).offset(skip).limit(limit).all()
    elif current_user:
        # Logged in users see their own imports plus all approved ones
        imports = db.query(models.BGeigieImport).join(models.User).filter(
            (models.BGeigieImport.user_id == current_user.id) | 
            (models.BGeigieImport.status == 'approved')
        ).offset(skip).limit(limit).all()
    else:
        # Anonymous users see only approved imports
        imports = db.query(models.BGeigieImport).join(models.User).filter(
            models.BGeigieImport.status == 'approved'
        ).offset(skip).limit(limit).all()
    
    # Convert to dict format with user information
    result = []
    for imp in imports:
        imp_dict = {
            "id": imp.id,
            "source": imp.source,
            "user_id": imp.user_id,
            "status": imp.status,
            "name": imp.name,
            "description": imp.description,
            "cities": imp.cities,
            "credits": imp.credits,
            "subtype": imp.subtype,
            "measurements_count": imp.measurements_count,
            "lines_count": imp.lines_count,
            "approved": imp.approved,
            "rejected": imp.rejected,
            "created_at": imp.created_at,
            "user_name": imp.user.name if imp.user else None,
            "user_email": imp.user.email if imp.user else None
        }
        result.append(imp_dict)
    
    return result


@router.get("/{import_id}")
async def get_import(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """Get individual import data"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id
    ).first()
    
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    return {
        "id": db_import.id,
        "source": db_import.source,
        "status": db_import.status,
        "measurements_count": db_import.measurements_count,
        "created_at": db_import.created_at,
        "user_id": db_import.user_id,
        "name": db_import.name,
        "cities": db_import.cities,
        "credits": db_import.credits,
        "description": db_import.description,
        "approved": db_import.approved,
        "rejected": db_import.rejected,
        "approved_by": db_import.approved_by,
        "rejected_by": db_import.rejected_by
    }


@router.get("/{import_id}/detail", response_class=HTMLResponse)
async def get_import_detail(
    import_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """Display detailed view with map for a bGeigie import"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id
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
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """Get measurement data for map visualization"""
    db_import = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == import_id
    ).first()
    
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Get measurements from measurements table
    measurements = db.query(models.Measurement).filter(
        models.Measurement.bgeigie_import_id == import_id
    ).all()
    
    measurement_data = []
    for m in measurements:
        measurement_data.append({
            "id": m.id,
            "cpm": m.cpm,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "altitude": m.altitude,
            "captured_at": m.captured_at.isoformat() if m.captured_at else "",
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
    
    # Allow metadata updates for processed/unprocessed (submits for approval) and approved (just save)
    if db_import.status not in ["processed", "unprocessed", "approved"]:
        raise HTTPException(status_code=400, detail="Import must be processed, unprocessed, or approved to edit metadata")
    
    # Update metadata fields
    for field, value in metadata.dict(exclude_unset=True).items():
        setattr(db_import, field, value)
    
    # Status transition
    # If already approved, keep approved; otherwise, submitting metadata moves to submitted
    if db_import.status in ["processed", "unprocessed", "rejected", "submitted"]:
        db_import.status = "submitted"
    
    db.commit()
    db.refresh(db_import)
    
    # Send email notification to the import owner
    try:
        await send_bgeigie_notification_email(
            recipient_email=db_import.user.email,
            recipient_name=db_import.user.name or db_import.user.email,
            action="submitted",
            import_id=db_import.id,
            import_filename=db_import.source
        )
    except Exception as e:
        print(f"Failed to send submission email: {e}")
    
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
                'altitude': m.get('altitude'),
                'captured_at': m['captured_at'],
            }
            for m in measurements_data
        ]

        if filtered_measurements:
            # Create measurement records
            crud.create_measurements(db=db, measurements=filtered_measurements, bgeigie_import_id=db_bgeigie_import.id)
            
            # Update import with measurement count and max CPM
            max_cpm = max([m['cpm'] for m in filtered_measurements]) if filtered_measurements else 0
            db_bgeigie_import.measurements_count = len(filtered_measurements)
            db_bgeigie_import.status = "processed"
            
            # Remove auto-approval to allow metadata entry
            # Auto-approval logic disabled to preserve metadata workflow
            # if should_auto_approve(filtered_measurements, max_cpm):
            #     db_bgeigie_import.status = "approved"
            #     db_bgeigie_import.approved_at = datetime.utcnow()
            #     db_bgeigie_import.approved_by = "auto-approval"
            
            db.commit()
            db.refresh(db_bgeigie_import)

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Only UTF-8 is supported.")
    except Exception as e:
        # Here you might want to delete the bgeigie_import record if parsing fails
        raise HTTPException(status_code=500, detail=f"Failed to parse and process file: {e}")

    return db_bgeigie_import

@router.patch("/{id}/submit")
async def submit_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "submitted", current_user.id)
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Send email notification to the import owner
    try:
        await send_bgeigie_notification_email(
            recipient_email=db_import.user.email,
            recipient_name=db_import.user.name or db_import.user.email,
            action="submitted",
            import_id=db_import.id,
            import_filename=db_import.source
        )
    except Exception as e:
        print(f"Failed to send submission email: {e}")
    
    return db_import

@router.patch("/{id}/approve")
async def approve_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "approved")
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Send email notification to the import owner
    try:
        await send_bgeigie_notification_email(
            recipient_email=db_import.user.email,
            recipient_name=db_import.user.name or db_import.user.email,
            action="approved",
            import_id=db_import.id,
            import_filename=db_import.source,
            admin_name=current_user.name or current_user.email
        )
    except Exception as e:
        print(f"Failed to send approval email: {e}")
    
    return db_import

@router.patch("/{id}/reject")
async def reject_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_import = crud.update_bgeigie_import_status(db, id, "rejected")
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Send email notification to the import owner
    try:
        await send_bgeigie_notification_email(
            recipient_email=db_import.user.email,
            recipient_name=db_import.user.name or db_import.user.email,
            action="rejected",
            import_id=db_import.id,
            import_filename=db_import.source,
            admin_name=current_user.name or current_user.email
        )
    except Exception as e:
        print(f"Failed to send rejection email: {e}")
    
    return db_import

@router.patch("/{id}/process")
async def process_bgeigie_import(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    """Manually trigger processing of an uploaded bGeigie import"""
    # Get the import record
    db_import = db.query(models.BGeigieImport).filter(models.BGeigieImport.id == id).first()
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Read file content from disk
    file_path = f"uploads/{db_import.source}"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            decoded_content = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="File not found on disk")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Parse the file and create measurements
    try:
        measurements_data = bgeigie_parser.parse_bgeigie_log(decoded_content)
        
        # Filter data to match the Measurement model
        filtered_measurements = [
            {
                'cpm': m['cpm'],
                'latitude': m['latitude'],
                'longitude': m['longitude'],
                'altitude': m.get('altitude'),
                'captured_at': m['captured_at'],
            }
            for m in measurements_data
        ]

        if filtered_measurements:
            # Delete existing measurements for this import
            db.query(models.Measurement).filter(models.Measurement.bgeigie_import_id == id).delete()
            
            # Create new measurement records
            crud.create_measurements(db=db, measurements=filtered_measurements, bgeigie_import_id=id)
            
            # Update import with measurement count and status
            db_import.measurements_count = len(filtered_measurements)
            db_import.status = "processed"
            db.commit()
            db.refresh(db_import)
            
            # Send email notification to the import owner
            try:
                await send_bgeigie_notification_email(
                    recipient_email=db_import.user.email,
                    recipient_name=db_import.user.name or db_import.user.email,
                    action="processed",
                    import_id=db_import.id,
                    import_filename=db_import.source
                )
            except Exception as e:
                print(f"Failed to send processing email: {e}")
            
            return {"message": f"Successfully processed {len(filtered_measurements)} measurements", "import": db_import}
        else:
            raise HTTPException(status_code=400, detail="No valid measurements found in file")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Only UTF-8 is supported.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse and process file: {e}")

@router.delete("/{id}")
async def delete_bgeigie_import(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a bGeigie import and all associated measurements"""
    print(f"Attempting to delete import {id} for user {current_user.id}")
    
    # First, get the import record regardless of owner to produce clearer diagnostics
    db_import_any = db.query(models.BGeigieImport).filter(
        models.BGeigieImport.id == id
    ).first()

    if not db_import_any:
        print(f"Import {id} not found in database")
        raise HTTPException(status_code=404, detail="Import not found")

    if db_import_any.user_id != current_user.id:
        # Allow admins to delete any import
        if getattr(current_user, 'role', None) == 'admin':
            print(f"Admin user {current_user.id} overriding ownership to delete import {id} owned by {db_import_any.user_id}")
        else:
            print(f"Import {id} owned by user {db_import_any.user_id}, not current user {current_user.id}")
            raise HTTPException(status_code=403, detail="Import not owned by user")

    # Owned by current user
    db_import = db_import_any
    
    try:
        print(f"Deleting all related records for import {id}")
        
        # Get count of measurements to delete
        measurements_count = db.execute(text("SELECT COUNT(*) FROM measurements WHERE bgeigie_import_id = :import_id"), {"import_id": id}).scalar()
        print(f"Found {measurements_count} measurements to delete")
        
        # Force delete all measurements using raw SQL (ORM seems to have issues with large deletes)
        db.execute(text("DELETE FROM measurements WHERE bgeigie_import_id = :import_id"), {"import_id": id})
        db.flush()
        print(f"Force deleted measurements using raw SQL")
        
        # Delete devices using raw SQL for consistency
        db.execute(text("DELETE FROM devices WHERE bgeigie_import_id = :import_id"), {"import_id": id})
        db.flush()
        print(f"Force deleted devices using raw SQL")
        
        # Delete bgeigie_logs using raw SQL
        db.execute(text("DELETE FROM bgeigie_logs WHERE bgeigie_import_id = :import_id"), {"import_id": id})
        db.flush()
        print(f"Force deleted bgeigie_logs using raw SQL")
        
        # Verify all child records are actually deleted
        remaining_measurements = db.execute(text("SELECT COUNT(*) FROM measurements WHERE bgeigie_import_id = :import_id"), {"import_id": id}).scalar()
        remaining_devices = db.execute(text("SELECT COUNT(*) FROM devices WHERE bgeigie_import_id = :import_id"), {"import_id": id}).scalar()
        remaining_logs = db.execute(text("SELECT COUNT(*) FROM bgeigie_logs WHERE bgeigie_import_id = :import_id"), {"import_id": id}).scalar()
        print(f"Remaining after deletes — measurements: {remaining_measurements}, devices: {remaining_devices}, logs: {remaining_logs}")
        
        if remaining_measurements > 0 or remaining_devices > 0 or remaining_logs > 0:
            raise Exception(
                f"Child rows still present (measurements={remaining_measurements}, devices={remaining_devices}, logs={remaining_logs})"
            )
        
        # Commit child deletions before deleting parent to satisfy FK constraints in DuckDB
        db.commit()
        print("Committed child deletions")

        # Now delete the import record using ORM (new transaction)
        db.refresh(db_import)
        db.delete(db_import)
        db.commit()
        print(f"Successfully deleted import {id}")
        
        # Send email notification to the import owner
        try:
            await send_bgeigie_notification_email(
                recipient_email=db_import.user.email,
                recipient_name=db_import.user.name or db_import.user.email,
                action="deleted",
                import_id=db_import.id,
                import_filename=db_import.source
            )
        except Exception as e:
            print(f"Failed to send deletion email: {e}")
        
        # Try to delete the uploaded file
        file_path = f"uploads/{db_import.source}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        
        return {"message": "Import deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting import {id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete import: {str(e)}")
