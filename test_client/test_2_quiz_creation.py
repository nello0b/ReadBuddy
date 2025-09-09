import requests
import time
import os

# Simple test script for creating a quiz from uploaded images

BASE_URL = "http://localhost:8000"
USER_ID = "google-oauth2|108917841066611392702"

IMAGE_DIR = "images"
IMAGE_FILES = [os.path.join(IMAGE_DIR, f"informational{i}.png") for i in range(1, 4)]
CATEGORY = "quiz_creation_test"


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


def create_quiz(category, num_questions, lang):
    url = f"{BASE_URL}/api/quiz/create/{category}/{USER_ID}/{num_questions}/{lang}"
    try:
        resp = requests.post(url)
        resp.raise_for_status()
        return resp.json().get("task_id")
    except Exception as e:
        print(f"❌ Failed to create quiz: {e}")
        return None


def get_quiz(quiz_id):
    url = f"{BASE_URL}/api/quiz/{quiz_id}/{USER_ID}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("quiz")
    except Exception as e:
        print(f"❌ Failed to get quiz {quiz_id}: {e}")
        return None


def get_questions(question_ids):
    url = f"{BASE_URL}/api/questions/batch/{USER_ID}"
    try:
        resp = requests.post(url, json={"question_ids": question_ids})
        resp.raise_for_status()
        return resp.json().get("questions")
    except Exception as e:
        print(f"❌ Failed to get questions: {e}")
        return None


def delete_quiz(quiz_id):
    url = f"{BASE_URL}/api/quiz/{quiz_id}/{USER_ID}"
    try:
        resp = requests.delete(url)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to delete quiz {quiz_id}: {e}")
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
    Main function to test quiz creation workflow from uploaded images.
    
    This function performs a complete end-to-end test of the ReadBuddy quiz creation system:
    1. Uploads multiple images for processing
    2. Waits for all processing tasks to complete
    3. Updates extraction categories for quiz grouping
    4. Creates a quiz from the processed content
    5. Validates the quiz and questions
    6. Cleans up all created resources
    """
    # Initialize timing and tracking variables
    start_time = time.time()
    task_map = {}  # Dictionary to track task information: {task_id: {extraction_id: id}}
    extraction_ids = []  # List of extraction IDs for cleanup
    quiz_id = None  # ID of created quiz for cleanup
    test_passed = False  # Flag to track if test completed successfully
    
    try:
        # Phase 1: Upload all images and get task IDs
        print("🚀 Phase 1: Uploading images for processing...")
        for img in IMAGE_FILES:
            print(f"📤 Uploading {img} ...")
            task_id = upload_image(img)
            if not task_id:
                return
            task_map[task_id] = {}

        # Phase 2: Wait for all image processing tasks to complete
        print("⏳ Phase 2: Waiting for image processing to complete...")
        for task_id in task_map:
            print(f"⏳ Waiting for task {task_id} ...")
            result = wait_for_task(task_id)
            if not result or result.get("state") != "SUCCESS":
                print(f"❌ Task {task_id} failed: {result}")
                return
            extraction_id = result.get("result")
            task_map[task_id]["extraction_id"] = extraction_id

        # Phase 3: Retrieve and validate extraction results
        print("📥 Phase 3: Retrieving extraction results...")
        for info in task_map.values():
            extraction_id = info["extraction_id"]
            print(f"📥 Getting extraction {extraction_id} ...")
            extraction = get_extraction(extraction_id)
            if not extraction:
                return
            extraction_ids.append(extraction_id)

        # Phase 4: Update categories to group extractions for quiz creation
        print("🏷️ Phase 4: Updating extraction categories...")
        for extraction_id in extraction_ids:
            if not update_category(extraction_id, CATEGORY):
                return

        # Phase 5: Create quiz from categorized extractions
        print("📝 Phase 5: Creating quiz from processed content...")
        quiz_task = create_quiz(CATEGORY, 3, "Hebrew")
        if not quiz_task:
            return

        # Wait for quiz creation to complete
        quiz_result = wait_for_task(quiz_task)
        if not quiz_result or quiz_result.get("state") != "SUCCESS":
            print(f"❌ Quiz creation failed: {quiz_result}")
            return

        quiz_id = quiz_result.get("result")
        print(f"📚 Quiz created: {quiz_id}")

        # Phase 6: Validate quiz structure and content
        print("✅ Phase 6: Validating quiz and questions...")
        quiz = get_quiz(quiz_id)
        if not quiz:
            return
        
        # Verify quiz has expected number of questions and correct category
        question_ids = quiz.get("question_ids", [])
        if len(question_ids) != 3 or quiz.get("category") != CATEGORY:
            print("❌ Quiz data not as expected")
            return

        # Retrieve and validate all questions
        questions = get_questions(question_ids)
        if not questions or len(questions) != 3:
            print("❌ Failed to retrieve questions")
            return

        # Check if questions contain Hebrew characters (since quiz language is Hebrew)
        def contains_hebrew(text):
            """Check if text contains Hebrew characters (Unicode range: 0x0590-0x05FF)"""
            if not text:
                return False
            return any('\u0590' <= char <= '\u05FF' for char in text)

        hebrew_validation_passed = True
        for i, question in enumerate(questions):
            print(f"🔍 Validating question {i+1}")
            question_text = question.get("content", "")  # Updated to match the correct key
            if not contains_hebrew(question_text):
                print(f"❌ Question {i+1} does not contain Hebrew characters: {question_text[:50]}...")
                hebrew_validation_passed = False
            else:
                print(f"✅ Question {i+1} contains Hebrew characters")

        if not hebrew_validation_passed:
            print("❌ Hebrew character validation failed")
            return

        print("✅ Quiz and questions retrieved successfully with Hebrew content validated")
        test_passed = True

    finally:
        # Phase 7: Cleanup - remove created resources
        print("\n🧹 Phase 7: Starting cleanup...")
        cleanup_success = True
        
        # Delete quiz if it was created
        if quiz_id:
            if delete_quiz(quiz_id):
                print("🗑️ Quiz deleted successfully")
            else:
                print("❌ Failed to delete quiz during cleanup")
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
