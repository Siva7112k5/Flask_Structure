import os
import uuid
from PIL import Image
from flask import current_app, url_for
import io
import base64

# Import cloud storage based on environment
if os.environ.get('VERCEL_ENV') == 'production':
    # For Vercel production - use Vercel Blob or S3
    try:
        from vercel_blob import put  # Vercel Blob Storage
        USE_CLOUD = True
        print("✅ Using Vercel Blob Storage")
    except ImportError:
        # Fallback to base64 encoding (embed images in database)
        USE_CLOUD = False
        print("⚠️ No cloud storage, using base64 encoding")
else:
    # Local development - use filesystem
    USE_CLOUD = False
    print("📁 Using local filesystem for uploads")

def save_review_images(files, review_id):
    """Save multiple review images and return their URLs/paths"""
    saved_images = []
    
    for file in files:
        if not file or not file.filename:
            continue
            
        # Check file extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
            continue
            
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        filename = f"{unique_id}.{ext}"
        
        if USE_CLOUD and os.environ.get('VERCEL_ENV') == 'production':
            # === OPTION 1: Vercel Blob Storage ===
            try:
                # Read file data
                file.seek(0)
                file_data = file.read()
                
                # Upload to Vercel Blob
                blob_result = put(
                    f"reviews/{review_id}/{filename}", 
                    file_data, 
                    {
                        'access': 'public',
                        'addRandomSuffix': False
                    }
                )
                
                # Get the public URL
                image_url = blob_result['url']
                
                # Create thumbnail (optional - could also upload thumbnail)
                try:
                    # Create thumbnail in memory
                    img = Image.open(io.BytesIO(file_data))
                    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    
                    # Save thumbnail to bytes
                    thumb_bytes = io.BytesIO()
                    img.save(thumb_bytes, format='JPEG' if ext.lower() == 'jpg' else ext.upper(), 
                            optimize=True, quality=85)
                    thumb_bytes.seek(0)
                    
                    # Upload thumbnail
                    thumb_result = put(
                        f"reviews/{review_id}/thumb_{filename}", 
                        thumb_bytes.getvalue(),
                        {'access': 'public', 'addRandomSuffix': False}
                    )
                    
                    # Store thumbnail URL (optional)
                    # image_url = thumb_result['url']  # Use thumbnail if preferred
                    
                except Exception as e:
                    print(f"⚠️ Thumbnail creation failed: {e}")
                
                saved_images.append(image_url)
                print(f"✅ Uploaded to Vercel Blob: {image_url}")
                
            except Exception as e:
                print(f"❌ Vercel Blob upload failed: {e}")
                # Fallback to base64
                saved_images.append(fallback_to_base64(file))
        
        elif os.environ.get('USE_S3', '').lower() == 'true':
            # === OPTION 2: AWS S3 ===
            try:
                import boto3
                from botocore.exceptions import NoCredentialsError
                
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.environ.get('AWS_REGION', 'us-east-1')
                )
                
                bucket_name = os.environ.get('S3_BUCKET_NAME')
                
                # Upload to S3
                file.seek(0)
                s3_key = f"reviews/{review_id}/{filename}"
                
                s3_client.upload_fileobj(
                    file, 
                    bucket_name, 
                    s3_key,
                    ExtraArgs={'ACL': 'public-read'}
                )
                
                # Generate URL
                if os.environ.get('CLOUDFRONT_URL'):
                    image_url = f"{os.environ.get('CLOUDFRONT_URL')}/{s3_key}"
                else:
                    image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                
                saved_images.append(image_url)
                print(f"✅ Uploaded to S3: {image_url}")
                
            except Exception as e:
                print(f"❌ S3 upload failed: {e}")
                saved_images.append(fallback_to_base64(file))
        
        else:
            # === OPTION 3: Local filesystem (development only) ===
            try:
                # Create directory for review images
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', str(review_id))
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save original
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                # Create thumbnail
                try:
                    img = Image.open(filepath)
                    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    thumb_path = os.path.join(upload_dir, f"thumb_{filename}")
                    img.save(thumb_path, optimize=True, quality=85)
                except Exception as e:
                    print(f"⚠️ Thumbnail creation failed: {e}")
                
                # Store relative path (for database)
                rel_path = os.path.join('uploads', 'reviews', str(review_id), filename).replace('\\', '/')
                saved_images.append(rel_path)
                print(f"✅ Saved locally: {rel_path}")
                
            except Exception as e:
                print(f"❌ Local save failed: {e}")
    
    return saved_images

def fallback_to_base64(file):
    """Fallback method: Convert image to base64 and store in database"""
    try:
        file.seek(0)
        file_data = file.read()
        
        # Optimize image
        img = Image.open(io.BytesIO(file_data))
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        format = img.format or 'JPEG'
        img.save(output, format=format, optimize=True, quality=80)
        output.seek(0)
        
        # Convert to base64
        encoded = base64.b64encode(output.getvalue()).decode('utf-8')
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        mime_type = f"image/{ext.replace('jpg', 'jpeg')}"
        
        return f"data:{mime_type};base64,{encoded}"
        
    except Exception as e:
        print(f"❌ Base64 conversion failed: {e}")
        return None

def delete_review_image(image_url, review_id):
    """Delete an uploaded image"""
    try:
        if image_url.startswith('data:'):
            # Base64 image - nothing to delete
            return True
            
        elif 'vercel-storage.com' in image_url:
            # Vercel Blob - needs API call
            from vercel_blob import delete
            delete(image_url)
            print(f"✅ Deleted from Vercel Blob: {image_url}")
            
        elif 'amazonaws.com' in image_url or image_url.startswith('http'):
            # S3 URL - extract key and delete
            import boto3
            s3_client = boto3.client('s3')
            bucket_name = os.environ.get('S3_BUCKET_NAME')
            
            # Extract key from URL
            key = '/'.join(image_url.split('/')[3:])
            s3_client.delete_object(Bucket=bucket_name, Key=key)
            print(f"✅ Deleted from S3: {key}")
            
        else:
            # Local file
            filepath = os.path.join(current_app.root_path, 'static', image_url)
            if os.path.exists(filepath):
                os.remove(filepath)
                # Also delete thumbnail
                thumb_path = filepath.replace('.', '/thumb_.')  # Adjust as needed
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                print(f"✅ Deleted locally: {filepath}")
                
        return True
        
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        return False