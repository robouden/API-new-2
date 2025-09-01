from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from .config import settings

# Use existing email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fastmail = FastMail(conf)

async def send_bgeigie_notification_email(
    recipient_email: str,
    recipient_name: str,
    action: str,
    import_id: int,
    import_filename: str,
    admin_name: str = None
):
    """
    Send notification email for bGeigie import actions
    
    Args:
        recipient_email: Email of the user who owns the import
        recipient_name: Name of the user
        action: One of 'approved', 'rejected', 'submitted', 'deleted', 'processed'
        import_id: ID of the bGeigie import
        import_filename: Original filename of the import
        admin_name: Name of admin who performed the action (for approve/reject)
    """
    
    # Email subject and content based on action
    if action == "approved":
        subject = f"Your bGeigie Import #{import_id} has been Approved"
        body = f"""
        <html>
        <body>
            <h2>Import Approved</h2>
            <p>Dear {recipient_name},</p>
            <p>Great news! Your bGeigie import has been approved and is now live on the Safecast map.</p>
            
            <h3>Import Details:</h3>
            <ul>
                <li><strong>Import ID:</strong> #{import_id}</li>
                <li><strong>Filename:</strong> {import_filename}</li>
                <li><strong>Status:</strong> Approved</li>
                <li><strong>Approved by:</strong> {admin_name or 'Admin'}</li>
            </ul>
            
            <p>Thank you for contributing to the Safecast community!</p>
            
            <p>Best regards,<br>
            The Safecast Team</p>
        </body>
        </html>
        """
        
    elif action == "rejected":
        subject = f"Your bGeigie Import #{import_id} has been Rejected"
        body = f"""
        <html>
        <body>
            <h2>Import Rejected</h2>
            <p>Dear {recipient_name},</p>
            <p>We regret to inform you that your bGeigie import has been rejected.</p>
            
            <h3>Import Details:</h3>
            <ul>
                <li><strong>Import ID:</strong> #{import_id}</li>
                <li><strong>Filename:</strong> {import_filename}</li>
                <li><strong>Status:</strong> Rejected</li>
                <li><strong>Reviewed by:</strong> {admin_name or 'Admin'}</li>
            </ul>
            
            <p>Please review your data and feel free to submit a corrected version.</p>
            
            <p>Best regards,<br>
            The Safecast Team</p>
        </body>
        </html>
        """
        
    elif action == "submitted":
        subject = f"Your bGeigie Import #{import_id} has been Submitted for Review"
        body = f"""
        <html>
        <body>
            <h2>Import Submitted</h2>
            <p>Dear {recipient_name},</p>
            <p>Your bGeigie import has been successfully submitted for review.</p>
            
            <h3>Import Details:</h3>
            <ul>
                <li><strong>Import ID:</strong> #{import_id}</li>
                <li><strong>Filename:</strong> {import_filename}</li>
                <li><strong>Status:</strong> Submitted for Review</li>
            </ul>
            
            <p>Our team will review your submission and you'll receive another email once it's been approved or if any issues are found.</p>
            
            <p>Thank you for contributing to Safecast!</p>
            
            <p>Best regards,<br>
            The Safecast Team</p>
        </body>
        </html>
        """
        
    elif action == "processed":
        subject = f"Your bGeigie Import #{import_id} has been Processed"
        body = f"""
        <html>
        <body>
            <h2>Import Processed</h2>
            <p>Dear {recipient_name},</p>
            <p>Your bGeigie import has been successfully processed and is ready for metadata submission.</p>
            
            <h3>Import Details:</h3>
            <ul>
                <li><strong>Import ID:</strong> #{import_id}</li>
                <li><strong>Filename:</strong> {import_filename}</li>
                <li><strong>Status:</strong> Processed</li>
            </ul>
            
            <p>Please log in to add metadata and submit your import for final approval.</p>
            
            <p>Best regards,<br>
            The Safecast Team</p>
        </body>
        </html>
        """
        
    elif action == "deleted":
        subject = f"Your bGeigie Import #{import_id} has been Deleted"
        body = f"""
        <html>
        <body>
            <h2>Import Deleted</h2>
            <p>Dear {recipient_name},</p>
            <p>This is to confirm that your bGeigie import has been deleted.</p>
            
            <h3>Import Details:</h3>
            <ul>
                <li><strong>Import ID:</strong> #{import_id}</li>
                <li><strong>Filename:</strong> {import_filename}</li>
                <li><strong>Status:</strong> Deleted</li>
            </ul>
            
            <p>If you have any questions about this action, please contact our support team.</p>
            
            <p>Best regards,<br>
            The Safecast Team</p>
        </body>
        </html>
        """
    
    # Create message
    message = MessageSchema(
        subject=subject,
        recipients=[recipient_email],
        body=body,
        subtype="html"
    )
    
    try:
        await fastmail.send_message(message)
        print(f"Email sent successfully to {recipient_email} for {action} action on import #{import_id}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {str(e)}")
        return False
