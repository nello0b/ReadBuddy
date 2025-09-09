# Create a virtual environment
Write-Host "Creating a virtual environment..."
python -m venv venv

# Activate the virtual environment
Write-Host "Activating the virtual environment..."
. .\venv\Scripts\Activate.ps1

# Ensure Python uses UTF-8 for all input and output so emoji
# characters in the test scripts are handled correctly on
# Windows terminals using a different code page.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Install the requirements
Write-Host "Installing requirements from test_requirements.txt..."
pip install -r test_requirements.txt | Out-Null

# Run the test runner
Write-Host "Running all tests..."
python run_all_tests.py

Write-Host "All steps completed."
