import pytest
import os
import tempfile

# Add parent directory to sys.path to allow imports from Scripts
# This is a bit of a hack for pytest; cleaner solutions might involve project structure changes or pytest path settings
import sys
parent_dir_of_scripts = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir_of_scripts)

# Now try to import the app
try:
    from Scripts.api_server import app as flask_app
except ImportError as e:
    # Fallback if the above path adjustment isn't enough in some execution contexts
    # This assumes 'Scripts' is a direct subdirectory of the project root added to PYTHONPATH
    # or that the tests are run from the project root.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from Scripts.api_server import app as flask_app


@pytest.fixture(scope='module')
def app():
    """Instance of Main flask app"""
    # Setup a temporary upload folder for tests
    flask_app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='pytest_api_uploads_')
    flask_app.config['TESTING'] = True
    # Other test-specific configurations can be added here

    # Example: Ensure necessary analyzers are available or mocked if needed
    # This depends on how deep the tests go. For pure API endpoint tests,
    # the actual analysis logic might be mocked.
    if not flask_app.extensions.get('text_analyzer_available', True): # Assuming some flag in app
        print("Warning: TextAnalyzer not available for testing.")
    if not flask_app.extensions.get('image_analyzer_available', True):
        print("Warning: ImageAnalyzer not available for testing.")


    yield flask_app

    # Teardown: clean up the temporary upload folder
    try:
        if os.path.exists(flask_app.config['UPLOAD_FOLDER']):
            # Ensure it's a directory before trying to remove it with shutil
            if os.path.isdir(flask_app.config['UPLOAD_FOLDER']):
                import shutil
                shutil.rmtree(flask_app.config['UPLOAD_FOLDER'])
            else:
                os.remove(flask_app.config['UPLOAD_FOLDER']) # if it was a file by mistake
    except Exception as e:
        print(f"Error cleaning up test upload folder: {e}")


@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()

# Add a dummy text file fixture
@pytest.fixture
def dummy_text_file():
    fd, path = tempfile.mkstemp(suffix='.txt', text=True)
    with os.fdopen(fd, 'w') as tmp:
        tmp.write("This is a dummy text file for testing purposes.\n")
        tmp.write("It contains some sample text.\n")
        tmp.write("Western ethics, Ubuntu philosophy, Confucian ideals, Islamic principles.\n")
    yield path
    os.remove(path)

# Add a dummy image file fixture (e.g., a small PNG)
@pytest.fixture
def dummy_image_file():
    fd, path = tempfile.mkstemp(suffix='.png')
    # Create a minimal valid PNG file (1x1 pixel, black)
    # This avoids needing a full image library just for a placeholder
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
        0x0C, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
        0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    with os.fdopen(fd, 'wb') as tmp:
        tmp.write(png_data)
    yield path
    os.remove(path)

@pytest.fixture
def dummy_csv_file():
    fd, path = tempfile.mkstemp(suffix='.csv', text=True)
    with os.fdopen(fd, 'w') as tmp:
        tmp.write("text,category\n")
        tmp.write("\"This is text about individual rights.\",western\n")
        tmp.write("\"Ubuntu teaches community harmony.\",ubuntu\n")
    yield path
    os.remove(path)

# If you need to mock the actual analysis functions for API tests:
# @pytest.fixture(autouse=True) # autouse makes it apply to all tests in the module/session
# def mock_analysis_functions(mocker):
#     mocker.patch('Scripts.api_server.run_text_analysis', return_value={"mocked": "text_results"})
#     mocker.patch('Scripts.api_server.run_image_analysis', return_value={"mocked": "image_results"})
