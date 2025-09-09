import requests
import time
import os
import json
from datetime import datetime

# python3 summary_test.py

test_images = ["test1.png", "test2.png", "test3.png", "test4.png", "test5.png"]

user_id = "google-oauth2|108917841066611392702"

# Server configuration
BASE_URL = "http://localhost:8000"

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

def get_image_extraction_result(extraction_id, user_id):
    """Get the image extraction result"""
    url = f"{BASE_URL}/api/image-extraction-result/{extraction_id}/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting extraction result: {e}")
        return None
    
def get_summary_by_id(summary_id, user_id):
    """Get a summary by its ID"""
    url = f"{BASE_URL}/api/summary/{summary_id}/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting summary: {e}")
        return None

def create_summary_from_source(source_id, user_id):
    """Create a summary from a single source"""
    url = f"{BASE_URL}/api/summary/from-source/{source_id}/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating summary: {e}")
        return None

def main():
    """Main test function"""
    print("🤖 ReadBuddy Test Client")
    print("=" * 50)

    for i in range(len(test_images)):
        print(f"1️⃣ Uploading {test_images[i]}...")
        upload_result = upload_image(test_images[i], user_id)
        
        if not upload_result:
            print("❌ Failed to upload image")
            return
        
        task_id = upload_result.get('task_id')
        print(f"📤 Upload initiated. Task ID: {task_id}")
        
        # Step 2: Wait for processing to complete
        print("\n2️⃣ Waiting for image processing to complete...")
        task_result = wait_for_task_completion(task_id)
        
        if not task_result or task_result.get('state') != 'SUCCESS':
            print("❌ Image processing failed or timed out")
            return
        
        # Extract the extraction_id from the task result
        extraction_id = task_result.get('result')
        if not extraction_id:
            print("❌ Could not get extraction ID from task result")
            print("Task result:", task_result)
            return
        
        print(f"🖼️ Image processing completed! Extraction ID: {extraction_id}")

        # Step 3: Get the extraction result (or use cached data)
        print(f"\n3️⃣ Getting extraction result for ID: {extraction_id}...")
        extraction_result = get_image_extraction_result(extraction_id, user_id)
        
        if not extraction_result:
            print("❌ Failed to get extraction result")
            return
        
        print("📝 Extraction result retrieved successfully!")
            
        print(f"🔎 Content preview: {extraction_result.get('text_data', {}).get('content', 'No content')[:200]}...")
        
        # Step 4: Create summary (or use cached data)
        print(f"\n4️⃣ Creating summary from extraction result...")
        summary_result = create_summary_from_source(extraction_id, user_id)
        
        if not summary_result:
            print("❌ Failed to create summary")
            return
        
        summary_task_id = summary_result.get('task_id')
        print(f"📝 Summary creation initiated. Task ID: {summary_task_id}")
        
        # Step 5: Wait for summary to complete
        print("\n5️⃣ Waiting for summary creation to complete...")
        summary_task_result = wait_for_task_completion(summary_task_id)
        
        if not summary_task_result or summary_task_result.get('state') != 'SUCCESS':
            print("❌ Summary creation failed or timed out")
            return
        
        summary_id = summary_task_result.get('result', {})
        
        # Step 6: Retrive the summary content
        print(f"\n6️⃣ Summary content retrieved:")
        summary = get_summary_by_id(summary_id, user_id)
        
        # Step 7: Print the results
        print("\n" + "=" * 50)
        print("🏁 FINAL RESULTS")
        print("=" * 50)
        
        print(f"\n📄 Original extracted text:")
        print("-" * 30)
        content = extraction_result.get('text_data', {}).get('content', 'No content available')
        print(content)
        
        print(f"\n📝 Generated summary:")
        print("-" * 30)
        print(summary)
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
