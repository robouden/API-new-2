import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from . import models, crud, bgeigie_parser
from .database import SessionLocal

logger = logging.getLogger(__name__)

class BackgroundJobProcessor:
    """
    Background job processor for async file processing and notifications.
    Uses FastAPI's async capabilities with DuckDB for efficient processing.
    """
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.is_running = False
    
    async def start(self):
        """Start the background job processor."""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._process_jobs())
            logger.info("Background job processor started")
    
    async def stop(self):
        """Stop the background job processor."""
        self.is_running = False
        logger.info("Background job processor stopped")
    
    async def add_job(self, job_type: str, job_data: Dict[str, Any]):
        """Add a job to the processing queue."""
        job = {
            "id": f"{job_type}_{datetime.utcnow().timestamp()}",
            "type": job_type,
            "data": job_data,
            "created_at": datetime.utcnow(),
            "status": "queued"
        }
        await self.processing_queue.put(job)
        logger.info(f"Added job {job['id']} to queue")
        return job["id"]
    
    async def _process_jobs(self):
        """Main job processing loop."""
        while self.is_running:
            try:
                # Wait for job with timeout
                job = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                logger.info(f"Processing job {job['id']} of type {job['type']}")
                job["status"] = "processing"
                
                # Process job based on type
                if job["type"] == "process_bgeigie_import":
                    await self._process_bgeigie_import(job)
                elif job["type"] == "send_notification":
                    await self._send_notification(job)
                elif job["type"] == "validate_measurements":
                    await self._validate_measurements(job)
                
                job["status"] = "completed"
                job["completed_at"] = datetime.utcnow()
                logger.info(f"Completed job {job['id']}")
                
            except asyncio.TimeoutError:
                # No jobs in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing job: {e}")
                if 'job' in locals():
                    job["status"] = "failed"
                    job["error"] = str(e)
    
    async def _process_bgeigie_import(self, job: Dict[str, Any]):
        """Process a bGeigie import file asynchronously."""
        import_id = job["data"]["import_id"]
        
        db = SessionLocal()
        try:
            # Get the import record
            bgeigie_import = db.query(models.BGeigieImport).filter(
                models.BGeigieImport.id == import_id
            ).first()
            
            if not bgeigie_import:
                raise ValueError(f"Import {import_id} not found")
            
            # Read file from disk
            file_path = f"uploads/{bgeigie_import.source}"
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Parse measurements
            measurements_data = bgeigie_parser.parse_bgeigie_log(file_content)
            
            # Filter and validate measurements
            filtered_measurements = []
            for m in measurements_data:
                if self._is_valid_measurement(m):
                    filtered_measurements.append({
                        'cpm': m['cpm'],
                        'latitude': m['latitude'],
                        'longitude': m['longitude'],
                        'captured_at': m['captured_at'],
                    })
            
            if filtered_measurements:
                # Create measurement records
                crud.create_measurements(
                    db=db, 
                    measurements=filtered_measurements, 
                    bgeigie_import_id=import_id
                )
                
                # Update import status
                max_cpm = max([m['cpm'] for m in filtered_measurements])
                bgeigie_import.measurements_count = len(filtered_measurements)
                bgeigie_import.status = "processed"
                
                # Check for auto-approval
                from .routers.bgeigie_imports import should_auto_approve
                if should_auto_approve(filtered_measurements, max_cpm):
                    bgeigie_import.status = "approved"
                    bgeigie_import.approved_at = datetime.utcnow()
                    bgeigie_import.approved_by = "auto-approval"
                
                db.commit()
                
                # Queue notification job
                await self.add_job("send_notification", {
                    "type": "import_processed",
                    "import_id": import_id,
                    "user_id": bgeigie_import.user_id,
                    "status": bgeigie_import.status
                })
            
        finally:
            db.close()
    
    async def _send_notification(self, job: Dict[str, Any]):
        """Send notification (placeholder for email/webhook integration)."""
        notification_data = job["data"]
        
        # Log notification (in production, integrate with email service)
        logger.info(f"Notification: {notification_data['type']} for user {notification_data.get('user_id')}")
        
        # Simulate async notification sending
        await asyncio.sleep(0.1)
    
    async def _validate_measurements(self, job: Dict[str, Any]):
        """Validate measurement data quality."""
        measurements = job["data"]["measurements"]
        
        validation_results = {
            "total_measurements": len(measurements),
            "valid_gps": 0,
            "valid_cpm": 0,
            "outliers": []
        }
        
        for i, m in enumerate(measurements):
            # GPS validation
            if (abs(m['latitude']) > 0.001 and abs(m['longitude']) > 0.001 and
                -90 <= m['latitude'] <= 90 and -180 <= m['longitude'] <= 180):
                validation_results["valid_gps"] += 1
            
            # CPM validation
            if 0 <= m['cpm'] <= 10000:
                validation_results["valid_cpm"] += 1
            else:
                validation_results["outliers"].append(i)
        
        logger.info(f"Validation results: {validation_results}")
        return validation_results
    
    def _is_valid_measurement(self, measurement: Dict[str, Any]) -> bool:
        """Validate individual measurement data."""
        try:
            # Check required fields
            if not all(key in measurement for key in ['cpm', 'latitude', 'longitude', 'captured_at']):
                return False
            
            # Validate CPM range
            if not (0 <= measurement['cpm'] <= 50000):
                return False
            
            # Validate GPS coordinates
            lat, lon = measurement['latitude'], measurement['longitude']
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return False
            
            # Check for zero coordinates (invalid GPS)
            if abs(lat) < 0.001 and abs(lon) < 0.001:
                return False
            
            return True
            
        except (KeyError, TypeError, ValueError):
            return False

# Global background processor instance
background_processor = BackgroundJobProcessor()

async def start_background_processor():
    """Start the global background processor."""
    await background_processor.start()

async def stop_background_processor():
    """Stop the global background processor."""
    await background_processor.stop()

async def queue_bgeigie_processing(import_id: int):
    """Queue a bGeigie import for background processing."""
    return await background_processor.add_job("process_bgeigie_import", {
        "import_id": import_id
    })

async def queue_notification(notification_type: str, **kwargs):
    """Queue a notification for sending."""
    return await background_processor.add_job("send_notification", {
        "type": notification_type,
        **kwargs
    })
