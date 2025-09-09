import requests
import time
import os
import json
from datetime import datetime

# python3 no_text_test.py

test_images = ["test6.png"]

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
        
        # Step 2: Wating for the task to fail (as we uploaded a bad image)
        print("\n2️⃣ Waiting for image processing to complete...")
        task_result = wait_for_task_completion(task_id)
        
        if not task_result or task_result.get('state') != 'FAILURE':
            print("❌ Task did not fail as expected")
            return
        
        print(f"✅❌✅ Task failed as expected: {task_result.get('result', 'No error message')}")

        
        
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
