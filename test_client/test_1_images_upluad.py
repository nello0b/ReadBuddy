import requests
import time
import os
from datetime import datetime
from PIL import Image

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "google-oauth2|108917841066611392702"

# Paths of images to upload
IMAGE_DIR = "images"
IMAGE_FILES = [os.path.join(IMAGE_DIR, f"informational{i}.png") for i in range(1, 6)]

# Where to store downloaded files
DOWNLOAD_DIR = "downloads"

# Expected bounds for processed images (should match backend config)
MIN_DIMENSION = 50
MAX_DIMENSION = 10000

def upload_image(image_path):
    url = f"{BASE_URL}/api/process-image/{USER_ID}"
    if not os.path.exists(image_path):
        print(f"❌ Missing image {image_path}")
        return None
    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, "image/png")}
        try:
            resp = requests.post(url, files=files)
            resp.raise_for_status()
            return resp.json().get("task_id")
        except Exception as e:
            print(f"❌ Upload failed for {image_path}: {e}")
            return None

def check_task_status(task_id):
    url = f"{BASE_URL}/task-status/{task_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Error checking task {task_id}: {e}")
        return None

def wait_for_task(task_id, timeout=300):
    start = time.time()
    interval = 1
    checked = 0
    while time.time() - start < timeout:
        status = check_task_status(task_id)
        if not status:
            return None
        state = status.get("state")
        if state == "SUCCESS":
            return status
        if state in ["FAILURE", "REVOKED"]:
            return status
        time.sleep(interval)
        checked += 1
        if checked >= interval:
            interval *= 2
            checked = 0
    print("⏰ Task timeout")
    return None

def get_extraction(extraction_id):
    url = f"{BASE_URL}/api/image-extraction-result/{extraction_id}/{USER_ID}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to get extraction {extraction_id}: {e}")
        return None

def download_file(path, dest):
    url = f"{BASE_URL}/{path.lstrip('/') }"
    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"❌ Failed downloading {url}: {e}")
        return False

def delete_extraction(extraction_id):
    url = f"{BASE_URL}/api/image-extraction-result/{extraction_id}/{USER_ID}"
    try:
        resp = requests.delete(url)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"⚠️ Failed deleting extraction {extraction_id}: {e}")
        return False

def validate_extraction_structure(extraction, extraction_id):
    """
    Validate extraction data structure and content.
    
    Args:
        extraction: The extraction object to validate
        extraction_id: ID of the extraction for error reporting
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate that paragraphs and audio files match
    paragraphs = extraction.get("text_data", {}).get("paragraphs", [])
    audio_urls = extraction.get("audio_zip_urls", [])
    
    if len(paragraphs) != len(audio_urls):
        return False, f"Paragraph/audio count mismatch for extraction {extraction_id}: {len(paragraphs)} paragraphs vs {len(audio_urls)} audio files"
    
    return True, None

def validate_image_dimensions(image_path):
    """
    Validate that downloaded image dimensions are within expected bounds.
    
    Args:
        image_path: Path to the downloaded image file
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        with Image.open(image_path) as im:
            w, h = im.size
        
        if not (MIN_DIMENSION <= w <= MAX_DIMENSION and MIN_DIMENSION <= h <= MAX_DIMENSION):
            return False, f"Image size out of bounds: {w}x{h} (expected {MIN_DIMENSION}-{MAX_DIMENSION})"
        
        return True, None
    except Exception as e:
        return False, f"Failed to validate image dimensions: {e}"

def main():
    """
    Main function to test batch image processing workflow.
    
    This function performs a complete end-to-end test of the ReadBuddy image processing system:
    1. Uploads multiple images for processing
    2. Waits for all processing tasks to complete
    3. Downloads and validates the results
    4. Cleans up temporary files and database entries
    """
    # Initialize timing and setup download directory
    start_time = time.time()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Dictionary to track task information: {task_id: {image: path, extraction_id: id, downloads: [files]}}
    task_map = {}
    extraction_ids = []  # List of extraction IDs for cleanup
    test_passed = False  # Flag to track if test completed successfully

    try:
        # Phase 1: Upload all images and get task IDs
        print("🚀 Phase 1: Uploading images...")
        for img in IMAGE_FILES:
            print(f"📤 Uploading {img} ...")
            task_id = upload_image(img)
            if not task_id:
                return
            task_map[task_id] = {"image": img}

        # Phase 2: Wait for all processing tasks to complete
        print("⏳ Phase 2: Waiting for processing to complete...")
        for task_id in task_map:
            print(f"⏳ Waiting for task {task_id} ...")
            result = wait_for_task(task_id)
            if not result or result.get("state") != "SUCCESS":
                print(f"❌ Task {task_id} failed: {result}")
                return
            extraction_id = result.get("result")
            task_map[task_id]["extraction_id"] = extraction_id
            extraction_ids.append(extraction_id)

        # Phase 3: Retrieve results and perform validation checks
        print("📥 Phase 3: Retrieving and validating results...")
        for info in task_map.values():
            extraction_id = info["extraction_id"]
            print(f"📥 Getting extraction {extraction_id} ...")
            
            # Get extraction data from the API
            extraction = get_extraction(extraction_id)
            if not extraction:
                return
            
            # Validate extraction structure
            is_valid, error_msg = validate_extraction_structure(extraction, extraction_id)
            if not is_valid:
                print(f"❌ {error_msg}")
                return

            file_path = extraction.get("file_path")
            downloaded = []

            # Download and validate processed image if available
            if file_path:
                img_dest = os.path.join(DOWNLOAD_DIR, os.path.basename(file_path))
                if download_file(file_path, img_dest):
                    # Validate image dimensions
                    is_valid, error_msg = validate_image_dimensions(img_dest)
                    if not is_valid:
                        print(f"❌ {error_msg}")
                        return
                    downloaded.append(img_dest)

            # Download all generated audio files
            paragraphs = extraction.get("text_data", {}).get("paragraphs", [])
            audio_urls = extraction.get("audio_zip_urls", [])
            for url in audio_urls:
                dest = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
                if download_file(url, dest):
                    downloaded.append(dest)

            # Validate that we downloaded the expected number of files
            info["downloads"] = downloaded
            expected_files = len(paragraphs) + (1 if file_path else 0)
            if len(downloaded) != expected_files:
                print(f"❌ Download mismatch: expected {expected_files}, got {len(downloaded)}")
                return

        print("✅ All validations passed")
        test_passed = True

    finally:
        # Phase 4: Cleanup - remove downloaded files and extraction results
        print("\n🧹 Phase 4: Starting cleanup...")
        cleanup_success = True
        
        # Clean up downloaded files and extraction results
        print("🗑️ Deleting downloaded files and image extractions...")
        for info in task_map.values():
            # Clean up downloaded files
            for f in info.get("downloads", []):
                if os.path.exists(f):
                    try:
                        os.remove(f)
                        print(f"🗑️ Deleted file: {os.path.basename(f)}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete file {f}: {e}")
                        cleanup_success = False
            
            # Clean up extraction results
            if "extraction_id" in info:
                extraction_id = info["extraction_id"]
                if delete_extraction(extraction_id):
                    print(f"🗑️ Extraction {extraction_id} deleted successfully")
                else:
                    print(f"⚠️ Failed to delete extraction {extraction_id}")
                    cleanup_success = False
        
        # Calculate and display timing information
        elapsed = time.time() - start_time
        print(f"⏱️ Total execution time: {elapsed:.2f} seconds")
        
        # Display final test results
        if test_passed and cleanup_success:
            print("🏁 Test completed successfully")
        elif test_passed:
            print("⚠️ Test passed but cleanup had issues")
        else:
            print("❌ Test failed")

if __name__ == "__main__":
    main()
