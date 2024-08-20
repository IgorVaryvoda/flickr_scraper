import os
import argparse
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import face_recognition
import shutil

# Load environment variables
load_dotenv()

# R2 credentials
r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
r2_endpoint_url = os.getenv("R2_ENDPOINT_URL")
r2_bucket_name = "places"

# Initialize R2 client
s3_client = boto3.client(
    service_name='s3',
    endpoint_url=r2_endpoint_url,
    aws_access_key_id=r2_access_key_id,
    aws_secret_access_key=r2_secret_access_key
)

def detect_faces(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    return len(face_locations) > 0

def move_to_review(file_path, place_id):
    review_dir = Path.cwd() / "review" / str(place_id)
    review_dir.mkdir(parents=True, exist_ok=True)
    new_path = review_dir / os.path.basename(file_path)
    shutil.move(file_path, new_path)
    print(f"Moved {file_path} to review folder")
    return new_path

def upload_file(file_path, place_id, is_review=False):
    file_name = os.path.basename(file_path)
    r2_key = f"{'review/' if is_review else ''}{place_id}/{file_name}"

    try:
        s3_client.upload_file(file_path, r2_bucket_name, r2_key)
        print(f"Uploaded {file_name} to R2 bucket {r2_bucket_name} with key {r2_key}")
        return True
    except ClientError as e:
        print(f"Error uploading {file_name} to R2: {str(e)}")
        return False

def process_and_upload_image(file_path, place_id):
    if detect_faces(file_path):
        new_path = move_to_review(file_path, place_id)
        # return upload_file(new_path, place_id, is_review=True)
    else:
        return upload_file(file_path, place_id)

def upload_place_images(place_folder):
    place_id = os.path.basename(place_folder)
    print(f"Processing place ID: {place_id}")

    uploaded_count = 0
    failed_count = 0
    reviewed_count = 0

    for file_name in os.listdir(place_folder):
        file_path = os.path.join(place_folder, file_name)
        if os.path.isfile(file_path):
            if process_and_upload_image(file_path, place_id):
                uploaded_count += 1
                if "review" in str(file_path):
                    reviewed_count += 1
            else:
                failed_count += 1

    return place_id, uploaded_count, failed_count, reviewed_count

def main(max_workers):
    images_dir = Path.cwd() / "images"

    if not images_dir.exists():
        print(f"Error: {images_dir} does not exist.")
        return

    place_folders = [f for f in images_dir.iterdir() if f.is_dir()]

    total_uploaded = 0
    total_failed = 0
    total_reviewed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_place = {executor.submit(upload_place_images, str(folder)): folder for folder in place_folders}
        for future in as_completed(future_to_place):
            place_id, uploaded, failed, reviewed = future.result()
            total_uploaded += uploaded
            total_failed += failed
            total_reviewed += reviewed
            print(f"Place ID {place_id}: Uploaded {uploaded}, Failed {failed}, Reviewed {reviewed}")

    print(f"\nUpload complete. Total uploaded: {total_uploaded}, Total failed: {total_failed}, Total reviewed: {total_reviewed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload images to R2 storage with face detection")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent upload workers")
    args = parser.parse_args()

    main(args.workers)
