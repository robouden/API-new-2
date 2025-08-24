from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .. import crud, models, schemas, bgeigie_parser
from ..security import get_db, get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[schemas.BGeigieImport])
def read_bgeigie_imports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    imports = crud.get_bgeigie_imports_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return imports

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
