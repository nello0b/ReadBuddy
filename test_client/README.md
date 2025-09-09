# 🧪 ReadBuddy Test Client

The test client is a comprehensive testing suite for the ReadBuddy application, providing automated end-to-end testing, integration testing, and API validation. These tests ensure the reliability, performance, and correctness of all ReadBuddy features.

## Structure

- **`run_all_tests.py`**: A script to execute all test files in sequence and report their results.
- **`setup_and_run_tests.ps1`**: PowerShell script for test setup and execution.
- **`test_requirements.txt`**: Contains the dependencies required to run the tests.
- **`downloads/`**: A directory for storing downloaded test artifacts.
- **`images/`**: Contains images used for testing purposes.
- **`side_tests/`**: Additional test scripts and resources for edge cases.

## Prerequisites

1. Ensure Python is installed on your system.
2. Install the required dependencies by running:
   ```bash
   pip install -r test_requirements.txt
   ```

## Running Tests

To run all tests, execute the `run_all_tests.py` script:
```bash
python run_all_tests.py
```

### Individual Tests
You can also run individual test files directly. For example:
```bash
python test_1_images_upluad.py
```

## Test Results

- A successful test will output:
  ```
  🏁 Test completed successfully
  ```
- A test with warnings will output:
  ```
  ⚠️ Test passed but cleanup had issues
  ```
- A failed test will output an error message and details.

## Notes

- Ensure all required resources (e.g., images, downloads) are available in their respective directories.
- The `side_tests/` directory contains additional scripts for testing edge cases and specific scenarios.
