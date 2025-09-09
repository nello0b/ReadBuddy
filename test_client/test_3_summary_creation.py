import requests
import time
import os

# Test script for creating a summary from an uploaded image

BASE_URL = "http://localhost:8000"
USER_ID = "google-oauth2|108917841066611392702"
IMAGE_PATH = os.path.join("images", "informational4.png")


def upload_image(image_path):
    url = f"{BASE_URL}/api/process-image/{USER_ID}"
    if not os.path.exists(image_path):
        print(f"❌ Image {image_path} not found")
        return None
    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, "image/png")}
        try:
            resp = requests.post(url, files=files)
            resp.raise_for_status()
            return resp.json().get("task_id")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None


def check_task_status(task_id):
    url = f"{BASE_URL}/task-status/{task_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Status check failed: {e}")
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


def create_summary(source_id):
    url = f"{BASE_URL}/api/summary/from-source/{source_id}/{USER_ID}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("task_id")
    except Exception as e:
        print(f"❌ Failed to create summary: {e}")
        return None


def get_summary(summary_id):
    url = f"{BASE_URL}/api/summary/{summary_id}/{USER_ID}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to get summary {summary_id}: {e}")
        return None


def delete_summary(summary_id):
    url = f"{BASE_URL}/api/summaries/{summary_id}/{USER_ID}"
    try:
        resp = requests.delete(url)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to delete summary {summary_id}: {e}")
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


def validate_summary_structure(summary, expected_summary_id, expected_extraction_id):
    """
    Validate summary data structure and content.
    
    Args:
        summary: The summary object to validate
        expected_summary_id: Expected summary ID
        expected_extraction_id: Expected extraction ID in source_ids
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate summary ID matches
    if summary.get("id") != expected_summary_id:
        return False, "Summary ID mismatch"
    
    # Validate extraction ID is in source_ids
    if expected_extraction_id not in summary.get("source_ids", []):
        return False, "Extraction ID not found in summary source IDs"
    
    # Validate summary has content
    if not summary.get("content"):
        return False, "Summary content is empty"
    
    return True, None


def main():
    """
    Main function to test summary creation workflow from uploaded image.
    
    This function performs a complete end-to-end test of the ReadBuddy summary creation system:
    1. Uploads an image for processing
    2. Waits for image processing to complete
    3. Creates a summary from the extracted content
    4. Validates the summary structure and content
    5. Cleans up created resources
    """
    # Initialize timing and tracking variables
    start_time = time.time()
    extraction_id = None  # ID of the image extraction result for cleanup
    summary_id = None  # ID of created summary for cleanup
    test_passed = False  # Flag to track if test completed successfully
    
    try:
        # Phase 1: Upload image for processing
        print("🚀 Phase 1: Uploading image for processing...")
        print(f"📤 Uploading {IMAGE_PATH} ...")
        task_id = upload_image(IMAGE_PATH)
        if not task_id:
            return
        print(f"📤 Upload task started: {task_id}")

        # Phase 2: Wait for image processing to complete
        print("⏳ Phase 2: Waiting for image processing to complete...")
        result = wait_for_task(task_id)
        if not result or result.get("state") != "SUCCESS":
            print(f"❌ Extraction task failed: {result}")
            return
        extraction_id = result.get("result")
        print(f"✅ Extraction complete: {extraction_id}")

        # Phase 3: Retrieve and validate extraction result
        print("📥 Phase 3: Retrieving extraction result...")
        extraction = get_extraction(extraction_id)
        if not extraction:
            return
        print("📄 Got extraction result")

        # Phase 4: Create summary from extracted content
        print("📝 Phase 4: Creating summary from extracted content...")
        summary_task = create_summary(extraction_id)
        if not summary_task:
            return
        print(f"📝 Summary creation task: {summary_task}")

        # Wait for summary creation to complete
        summary_res = wait_for_task(summary_task)
        if not summary_res or summary_res.get("state") != "SUCCESS":
            print(f"❌ Summary task failed: {summary_res}")
            return
        summary_id = summary_res.get("result")
        print(f"✅ Summary created: {summary_id}")

        # Phase 5: Validate summary structure and content
        print("✅ Phase 5: Validating summary and content...")
        summary = get_summary(summary_id)
        if not summary:
            return
        print("📑 Retrieved summary")

        # Validate summary data structure
        is_valid, error_msg = validate_summary_structure(summary, summary_id, extraction_id)
        if not is_valid:
            print(f"❌ {error_msg}")
            return

        print("✅ Summary data validation passed")
        test_passed = True

    finally:
        # Phase 6: Cleanup - remove created resources
        print("\n🧹 Phase 6: Starting cleanup...")
        cleanup_success = True
        
        # Delete summary if it was created
        if summary_id:
            if delete_summary(summary_id):
                print("🗑️ Summary deleted successfully")
            else:
                print("❌ Failed to delete summary during cleanup")
                cleanup_success = False
        
        # Delete extraction result if it was created
        if extraction_id:
            if delete_extraction(extraction_id):
                print("🗑️ Extraction deleted successfully")
            else:
                print("⚠️ Failed to delete extraction during cleanup")
                cleanup_success = False
        
        # Calculate and display timing information
        end_time = time.time()
        total_time = end_time - start_time
        print(f"⏱️ Total execution time: {total_time:.2f} seconds")
        
        # Display final test results
        if test_passed and cleanup_success:
            print("🏁 Test completed successfully")
        elif test_passed:
            print("⚠️ Test passed but cleanup had issues")
        else:
            print("❌ Test failed")


if __name__ == "__main__":
    main()
