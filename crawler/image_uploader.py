import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_images(article_id: str, image_paths: list) -> dict:
    """
    Uploads a list of local images to Cloudflare R2.
    Returns a mapping of local paths to public R2 URLs.
    Deletes local files after successful upload.
    """
    results = {}
    
    # R2 Configuration
    endpoint_url = os.getenv("R2_ENDPOINT_URL")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")
    public_url_base = os.getenv("R2_PUBLIC_URL", "").rstrip('/')

    if not all([endpoint_url, access_key_id, secret_access_key, bucket_name]):
        print("Error: Cloudflare R2 environment variables are not fully configured.")
        return {}

    # Initialize S3 client for R2
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version='s3v4'),
        region_name='auto' # R2 uses 'auto'
    )

    for local_path in image_paths:
        try:
            if not os.path.exists(local_path):
                print(f"Warning: Local file not found: {local_path}")
                continue

            filename = os.path.basename(local_path)
            # R2 Key: {article_id}/{filename}
            r2_key = f"{article_id}/{filename}"
            
            # Determine Content-Type based on extension
            content_type = "image/jpeg"
            if filename.lower().endswith(".png"): content_type = "image/png"
            elif filename.lower().endswith(".gif"): content_type = "image/gif"
            elif filename.lower().endswith(".webp"): content_type = "image/webp"

            # Upload to R2
            print(f"Uploading {filename} to R2...")
            s3_client.upload_file(
                local_path, 
                bucket_name, 
                r2_key,
                ExtraArgs={'ContentType': content_type}
            )

            # Construct public URL
            public_url = f"{public_url_base}/{r2_key}"
            results[local_path] = public_url

            # Delete local file after success
            os.remove(local_path)
            print(f"Successfully uploaded and deleted local copy: {filename}")

        except Exception as e:
            print(f"Error uploading image {local_path}: {e}")
            continue

    return results

if __name__ == "__main__":
    # Test block (requires valid R2 credentials in .env)
    # create a dummy file to test
    dummy_path = "tmp/test_upload.txt"
    os.makedirs("tmp", exist_ok=True)
    with open(dummy_path, "w") as f:
        f.write("test upload")
    
    print("Testing uploader with dummy file...")
    # This will likely fail without real credentials, but demonstrates the logic
    res = upload_images("test-article", [dummy_path])
    print(f"Upload results: {res}")
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)
