import subprocess
import os

def run_tests():
    test_files = [
        "test_1_images_upluad.py",
        "test_2_quiz_creation.py",
        "test_3_summary_creation.py",
        "test_4_glossary_creation.py"
    ]

    for test_file in test_files:
        print(f"Running {test_file}...")
        result = subprocess.run(["python", test_file], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Test failed: {test_file}")
            print(result.stderr)
            continue

        # Check the last line of the output
        last_line = result.stdout.strip().split("\n")[-1]
        if last_line == "🏁 Test completed successfully":
            print(f"✅ {test_file} passed successfully.")
        elif last_line == "⚠️ Test passed but cleanup had issues":
            print(f"⚠️ {test_file} passed with warnings.")
        else:
            print(f"❌ Test failed: {test_file}")

if __name__ == "__main__":
    run_tests()
