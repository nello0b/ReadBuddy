import requests
import time
import os
 
# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "google-oauth2|108917841066611392702"

IMAGE_DIR = "images"
IMAGE_FILES = [os.path.join(IMAGE_DIR, f"informational{i}.png") for i in range(1, 6)]
CATEGORY = "glossary_creation_test"


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


def update_category(extraction_id, new_category):
    url = f"{BASE_URL}/api/image-extraction-result/update-category/{extraction_id}/{USER_ID}"
    try:
        resp = requests.put(url, json={"new_category": new_category})
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to update category for {extraction_id}: {e}")
        return False


def create_glossary(category, lang):
    url = f"{BASE_URL}/api/glossary/create/{category}/{USER_ID}/{lang}"
    try:
        resp = requests.post(url)
        resp.raise_for_status()
        return resp.json().get("task_id")
    except Exception as e:
        print(f"❌ Failed to create glossary: {e}")
        return None


def get_glossary(glossary_id):
    url = f"{BASE_URL}/api/glossary/by-id/{glossary_id}/{USER_ID}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("glossary")
    except Exception as e:
        print(f"❌ Failed to get glossary {glossary_id}: {e}")
        return None


def delete_glossary(glossary_id):
    url = f"{BASE_URL}/api/glossary/{glossary_id}/{USER_ID}"
    try:
        resp = requests.delete(url)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to delete glossary {glossary_id}: {e}")
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


def main():
    """
    Main function to test glossary creation workflow from uploaded images.
    
    This function performs a complete end-to-end test of the ReadBuddy glossary creation system:
    1. Uploads multiple images for processing
    2. Waits for all image processing to complete
    3. Retrieves and validates extraction results
    4. Updates extraction categories for glossary grouping
    5. Creates a glossary from the processed content
    6. Validates the glossary structure and content
    7. Cleans up created resources
    """
    # Initialize timing and tracking variables
    start_time = time.time()
    task_map = {}  # Dictionary to track task information: {task_id: {extraction_id: id}}
    extraction_ids = []  # List of extraction IDs for cleanup
    glossary_id = None  # ID of created glossary for cleanup
    test_passed = False  # Flag to track if test completed successfully

    try:
        # Phase 1: Upload images for processing
        print("🚀 Phase 1: Uploading images for processing...")
        for img in IMAGE_FILES:
            print(f"📤 Uploading {img} ...")
            task_id = upload_image(img)
            if not task_id:
                return
            task_map[task_id] = {}

        # Phase 2: Wait for image processing to complete
        print("⏳ Phase 2: Waiting for image processing to complete...")
        for task_id in task_map:
            print(f"⏳ Waiting for task {task_id} ...")
            result = wait_for_task(task_id)
            if not result or result.get("state") != "SUCCESS":
                print(f"❌ Extraction task failed: {result}")
                return
            extraction_id = result.get("result")
            task_map[task_id]["extraction_id"] = extraction_id
            print(f"✅ Extraction complete: {extraction_id}")

        # Phase 3: Retrieve and validate extraction results
        print("📥 Phase 3: Retrieving extraction results...")
        for info in task_map.values():
            extraction_id = info["extraction_id"]
            print(f"📥 Getting extraction {extraction_id} ...")
            extraction = get_extraction(extraction_id)
            if not extraction:
                return
            extraction_ids.append(extraction_id)
        print("📄 Got all extraction results")

        # Phase 4: Update extraction categories for glossary grouping
        print("🏷️ Phase 4: Updating extraction categories...")
        for extraction_id in extraction_ids:
            print(f"🏷️ Updating category for {extraction_id} to {CATEGORY}")
            if not update_category(extraction_id, CATEGORY):
                return
        print("✅ All categories updated successfully")

        # Phase 5: Create glossary from processed content
        print("📖 Phase 5: Creating glossary from processed content...")
        glossary_task = create_glossary(CATEGORY, "Hebrew")
        if not glossary_task:
            return
        print(f"📖 Glossary creation task: {glossary_task}")

        # Wait for glossary creation to complete
        glossary_result = wait_for_task(glossary_task)
        if not glossary_result or glossary_result.get("state") != "SUCCESS":
            print(f"❌ Glossary creation task failed: {glossary_result}")
            return

        glossary_id = glossary_result.get("result")
        print(f"✅ Glossary created: {glossary_id}")

        # Phase 6: Validate glossary structure and content
        print("✅ Phase 6: Validating glossary...")
        glossary = get_glossary(glossary_id)
        if not glossary:
            return
        print("📚 Retrieved glossary")

        # Validate glossary data structure
        if glossary.get("category") != CATEGORY:
            print("❌ Glossary category mismatch")
            return

        entries = glossary.get("entries", [])
        if not entries:
            print("❌ Glossary has no entries")
            return

        print("✅ Glossary data validation passed")
        print(f"📊 Glossary contains {len(entries)} entries")
        test_passed = True

    finally:
        # Phase 7: Cleanup - remove created resources
        print("\n🧹 Phase 7: Starting cleanup...")
        cleanup_success = True

        # Delete glossary if it was created
        if glossary_id:
            if delete_glossary(glossary_id):
                print("🗑️ Glossary deleted successfully")
            else:
                print("❌ Failed to delete glossary during cleanup")
                cleanup_success = False

        # Delete all extraction results
        print("🗑️ Deleting image extractions...")
        for extraction_id in extraction_ids:
            if delete_extraction(extraction_id):
                print(f"🗑️ Extraction {extraction_id} deleted successfully")
            else:
                print(f"⚠️ Failed to delete extraction {extraction_id}")
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
