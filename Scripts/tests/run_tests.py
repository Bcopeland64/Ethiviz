import pytest
import os
import sys

if __name__ == "__main__":
    # Ensure the project root is in PYTHONPATH so that 'Scripts.api_server' etc. can be found
    # This is crucial for the tests to import the application code correctly.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"Project root added to sys.path: {project_root}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")

    # Define the path to the test file
    # It's in the same directory as this run_tests.py script
    test_file_path = os.path.join(os.path.dirname(__file__), "test_backend.py")
    
    print(f"Attempting to run pytest on: {test_file_path}")

    if not os.path.exists(test_file_path):
        print(f"ERROR: Test file not found at {test_file_path}")
        sys.exit(1)
    
    # Arguments for pytest.main()
    # -v for verbose output
    # We are directly specifying the test file.
    # Pytest should pick up conftest.py from the same directory as test_backend.py
    args = [
        "-v", 
        test_file_path
    ]
    
    # Ensure conftest.py can be found by adding its directory to pytest's considerations
    # (though typically it's found automatically if in the test directory or an ancestor)
    # We can also try running pytest by changing CWD to where conftest.py is,
    # or by ensuring tests are run from a directory where conftest is discoverable.

    # Running pytest.main()
    # It's important that conftest.py is in the same directory as test_backend.py or an ancestor,
    # or that pytest is run in a way it can find conftest.py (e.g. from project root pointing to test dir)
    
    # Let's try running pytest by changing to the directory of the test file first
    # so conftest.py is definitely found
    test_dir = os.path.dirname(test_file_path)
    print(f"Changing CWD to: {test_dir} for pytest execution")
    original_cwd = os.getcwd()
    os.chdir(test_dir)

    # Now run pytest targeting the test file by its name, conftest.py should be in CWD.
    exit_code = pytest.main(["-v", "test_backend.py"])
    
    # Change back to original CWD
    os.chdir(original_cwd)

    sys.exit(exit_code)
