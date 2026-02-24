import os
import uuid
from PIL import Image
from flask import current_app

def save_review_images(files, review_id):
    """Save multiple review images and return their paths"""
    saved_images = []
    
    # Create directory for review images if it doesn't exist
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', str(review_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        if file and file.filename:
            # Check file extension
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
                continue
                
            # Generate unique filename
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Save original
            file.save(filepath)
            
            # Create thumbnail (optional)
            try:
                img = Image.open(filepath)
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                thumb_path = os.path.join(upload_dir, f"thumb_{filename}")
                img.save(thumb_path, optimize=True, quality=85)
            except:
                pass  # If thumbnail fails, just use original
            
            # Store relative path (for database)
            rel_path = os.path.join('uploads', 'reviews', str(review_id), filename).replace('\\', '/')
            saved_images.append(rel_path)
    
    return saved_images