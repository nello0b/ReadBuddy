import requests
import time
import os
import json
from datetime import datetime
from PIL import Image
from io import BytesIO

# Test script for image resizing functionality
# Tests images that are too small or too big to verify they get resized properly
# python3 image_too_small_too_big.py

test_images = ["test8.png","test9.png", "test1.png"]

user_id = "google-oauth2|108917841066611392702"

# Server configuration
BASE_URL = "http://localhost:8000"

# Expected dimension bounds (should match your backend config)
MIN_DIMENSION = 50  # Adjust to match your backend MIN_DIMENSION
MAX_DIMENSION = 10000  # Adjust to match your backend MAX_DIMENSION

def get_image_dimensions(image_path):
    """Get the dimensions of an image file"""
    try:
        with Image.open(image_path) as img:
            return img.size  # Returns (width, height)
    except Exception as e:
        print(f"❌ Error reading image dimensions: {e}")
        return None

def get_image_dimensions_from_bytes(img_bytes):
    """Get dimensions from raw image bytes"""
    try:
        with Image.open(BytesIO(img_bytes)) as img:
            return img.size
    except Exception as e:
        print(f"❌ Error reading image bytes: {e}")
        return None

def download_image(file_path):
    """Download an image from the backend"""
    url = f"{BASE_URL}/{file_path.lstrip('/')}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading image from {url}: {e}")
        return None

def get_extraction_result(result_id, user_id):
    """Get the extraction result details"""
    url = f"{BASE_URL}/api/image-extraction-result/{result_id}/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting extraction result: {e}")
        return None

def analyze_resize_result(original_size, new_size):
    """Check if the new image size fits within the valid bounds."""
    new_w, new_h = new_size

    # Check if the new size is within the valid range
    is_correct_size = MIN_DIMENSION <= new_w <= MAX_DIMENSION and MIN_DIMENSION <= new_h <= MAX_DIMENSION

    analysis = {
        "actual_size": (new_w, new_h),
        "correct": is_correct_size,
        "reason": f"Image resized to {new_w}x{new_h}, which is {'valid' if is_correct_size else 'invalid'}"
    }

    return analysis

def upload_image(image_path, user_id):
    """Upload an image for processing"""
    url = f"{BASE_URL}/api/process-image/{user_id}"
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file {image_path} not found")
        return None
    
    with open(image_path, 'rb') as file:
        files = {'file': (os.path.basename(image_path), file, 'image/png')}
        
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error uploading image: {e}")
            return None

def check_task_status(task_id):
    """Check the state of a task"""
    url = f"{BASE_URL}/task-status/{task_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking task status: {e}")
        return None

def wait_for_task_completion(task_id, max_wait_time=300):
    """Wait for a task to complete, checking every few seconds"""
    print(f"⏳ Waiting for task {task_id} to complete...")
    start_time = time.time()
    
    check_interval = 1
    times_checked_with_this_interval = 0
    while time.time() - start_time < max_wait_time:
        state = check_task_status(task_id)
        if not state:
            return None
            
        print(f"🔄 Task state: {state.get('state', 'UNKNOWN')}")
        
        if state.get('state') == 'SUCCESS':
            print("✅ Task completed successfully!")
            return state
        elif state.get('state') in ['FAILURE', 'REVOKED']:
            print(f"❌ Task failed: {state}")
            return state
        
        print(f"⌛ Task is still processing, seconds elapsed: {int(time.time() - start_time)}, ", end = "")
        print(f"sleeping for {check_interval} seconds before next check...")
        time.sleep(check_interval)
        times_checked_with_this_interval +=1
        if times_checked_with_this_interval >= check_interval:
            check_interval = check_interval * 2
            times_checked_with_this_interval = 0
    
    print("⏰ Task did not complete within the maximum wait time")
    return None

def main():
    """Main test function"""
    print("🤖 ReadBuddy Image Resize Test Client")
    print("=" * 50)
    print(f"📏 Testing with dimension bounds: {MIN_DIMENSION} - {MAX_DIMENSION} pixels")
    
    # Test images including one that should not be resized
    test_cases = [
        {"file": "test8.png", "description": "too small image (should be resized up)"},
        {"file": "test9.png", "description": "too big image (should be resized down)"},
        {"file": "test1.png", "description": "correctly sized image (no resize)"}
    ]

    total_tests = len(test_cases)
    for i, test_case in enumerate(test_cases):
        image_file = test_case["file"]
        description = test_case["description"]

        print(f"\n🔍 Test {i+1}/{total_tests}: Testing {description}")
        print(f"1️⃣ Analyzing original image: {image_file}")
        
        # Get original image dimensions
        original_size = get_image_dimensions(image_file)
        if not original_size:
            print("❌ Failed to read original image dimensions")
            continue
            
        original_width, original_height = original_size
        print(f"📐 Original size: {original_width}x{original_height} pixels")
        
        print(f"\n2️⃣ Uploading {image_file}...")
        upload_result = upload_image(image_file, user_id)
        
        if not upload_result:
            print("❌ Failed to upload image")
            continue
        
        task_id = upload_result.get('task_id')
        print(f"📤 Upload initiated. Task ID: {task_id}")
        
        # Step 3: Wait for the task to complete (should succeed with resizing)
        print(f"\n3️⃣ Waiting for image processing to complete...")
        task_result = wait_for_task_completion(task_id)
        
        if not task_result:
            print("❌ Task timed out")
            continue
            
        if task_result.get('state') == 'SUCCESS':
            print(f"✅ Test {i+1} PASSED: {description} was successfully processed!")
            result_id = task_result.get('result')

            if result_id:
                print(f"📄 Extraction result ID: {result_id}")

                extraction_result = get_extraction_result(result_id, user_id)
                if extraction_result:
                    print("📥 Downloading processed image...")
                    file_path = extraction_result.get("file_path")
                    img_bytes = download_image(file_path) if file_path else None
                    if img_bytes:
                        new_size = get_image_dimensions_from_bytes(img_bytes)
                        if new_size:
                            analysis = analyze_resize_result(original_size, new_size)
                            print(f"🔍 Analysis: {analysis['reason']}")
                            print(f"✅ Resize Correct: {analysis['correct']}")
                        else:
                            print("❌ Could not determine size of processed image")
                    else:
                        print("❌ Failed to download processed image")
                else:
                    print("ℹ️  Could not retrieve detailed processing results")
            else:
                print("📄 No result ID returned")
                
        elif task_result.get('state') == 'FAILURE':
            print(f"❌ Test {i+1} FAILED: {description} failed to process")
            error_msg = task_result.get('result', 'No error message')
            print(f"💥 Error: {error_msg}")
        else:
            print(f"⚠️  Test {i+1} UNKNOWN: Unexpected task state: {task_result.get('state')}")
            
        print("-" * 70)
    
    print("\n🏁 All tests completed!")
    print("Expected behavior: Images should be resized to fit within the valid bounds")
    print(f"📏 Size constraints: {MIN_DIMENSION}px - {MAX_DIMENSION}px for both width and height")

if __name__ == "__main__":
    main()
