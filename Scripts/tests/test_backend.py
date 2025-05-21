import pytest
import json
import time
import os
from unittest.mock import MagicMock, patch

# Assuming api_server.jobs is the global dictionary storing job statuses
# For direct inspection in tests. This is okay for this testing scope.
from Scripts.api_server import jobs as api_jobs

# Imports from test_analysis_logic
import pandas as pd # Required for some mock data creation if not already covered
import numpy as np  # Required for some mock data creation if not already covered

from Scripts.app import (
    run_text_analysis,
    run_image_analysis,
    create_tradition_radar_chart, # Original name, but refactored to return dict
    create_d3_visualization_data  # Refactored name
)
from Scripts.text_analyzer import TextAnalysisResult # For constructing mock results
from Scripts.image_analyzer import ImageAnalysisResult # For constructing mock results


# --- Fixtures from conftest.py are implicitly available ---
# We don't need to redefine app, client, dummy_text_file, etc. here

# --- Tests from test_api_server.py ---

def test_home_endpoint(client):
    """Test the home endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["message"] == "EthiViz API Server is running."

def test_submit_text_analysis_valid_file(client, dummy_text_file, mocker):
    """Test submitting a text analysis job with a valid text file."""
    mocker.patch('Scripts.api_server.run_text_analysis', return_value={"summary": "mocked text results"})
    data = {
        'analysis_type': 'text',
        'data_source_type': 'upload',
        'selected_traditions': ['western', 'ubuntu']
    }
    files = {'text_file': (open(dummy_text_file, 'rb'), os.path.basename(dummy_text_file))}
    response = client.post('/api/analyze', data=data, content_type='multipart/form-data', buffered=True, files=files)
    assert response.status_code == 202
    json_data = response.get_json()
    assert 'job_id' in json_data
    job_id = json_data['job_id']
    assert job_id in api_jobs
    assert api_jobs[job_id]['analysis_type'] == 'text'

def test_submit_image_analysis_valid_files(client, dummy_image_file, mocker):
    """Test submitting an image analysis job with a valid image file."""
    mocker.patch('Scripts.api_server.run_image_analysis', return_value={"summary": "mocked image results"})
    data = {
        'analysis_type': 'image',
        'data_source_type': 'upload',
        'selected_traditions': ['confucian']
    }
    files = {'image_files': [(open(dummy_image_file, 'rb'), 'test_image.png')]}
    response = client.post('/api/analyze', data=data, content_type='multipart/form-data', buffered=True, files=files)
    assert response.status_code == 202
    json_data = response.get_json()
    assert 'job_id' in json_data
    job_id = json_data['job_id']
    assert job_id in api_jobs
    assert api_jobs[job_id]['analysis_type'] == 'image'

def test_submit_analysis_missing_analysis_type(client):
    response = client.post('/api/analyze', data={'data_source_type': 'upload'})
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Missing 'analysis_type' parameter" in json_data['error']

def test_submit_analysis_invalid_analysis_type(client):
    response = client.post('/api/analyze', data={'analysis_type': 'invalid_type'})
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Invalid 'analysis_type'" in json_data['error']

def test_submit_text_analysis_missing_file(client):
    data = {'analysis_type': 'text', 'data_source_type': 'upload'}
    response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Missing 'text_file'" in json_data['error']

def test_submit_text_analysis_invalid_file_type(client, dummy_image_file):
    data = {'analysis_type': 'text', 'data_source_type': 'upload'}
    files = {'text_file': (open(dummy_image_file, 'rb'), 'test_image_as_text.png')}
    response = client.post('/api/analyze', data=data, content_type='multipart/form-data', buffered=True, files=files)
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Invalid text file type" in json_data['error']

def test_job_lifecycle_text_analysis(client, dummy_text_file, mocker):
    mocked_text_result = {"text_analysis": {"bias_score": 0.75, "diversity_index": 0.88}}
    mocker.patch('Scripts.api_server.run_text_analysis', return_value=mocked_text_result["text_analysis"])
    submit_data = {
        'analysis_type': 'text',
        'data_source_type': 'upload',
        'selected_traditions': ['western']
    }
    files = {'text_file': (open(dummy_text_file, 'rb'), 'test_lifecycle.txt')}
    submit_response = client.post('/api/analyze', data=submit_data, content_type='multipart/form-data', buffered=True, files=files)
    assert submit_response.status_code == 202
    submit_json = submit_response.get_json()
    job_id = submit_json['job_id']
    status_url = submit_json['status_url']
    max_polls = 20 # Increased polls slightly
    poll_interval = 0.1 # Reduced interval
    completed = False
    results_url = None # Initialize results_url
    for i in range(max_polls):
        time.sleep(poll_interval)
        status_response = client.get(status_url)
        assert status_response.status_code == 200
        status_json = status_response.get_json()
        if status_json['status'] == 'completed':
            completed = True
            results_url = status_json['results_url']
            break
        elif status_json['status'] == 'failed':
            pytest.fail(f"Job {job_id} failed: {status_json.get('error_message', 'Unknown error')}")
        assert status_json['status'] in ['pending', 'processing']
    if not completed:
        pytest.fail(f"Job {job_id} did not complete. Last status: {status_json['status']}")
    
    assert results_url is not None, "Results URL was not set." # Ensure results_url is set
    results_response = client.get(results_url)
    assert results_response.status_code == 200
    results_json = results_response.get_json()
    assert results_json['results']['text_analysis']['bias_score'] == 0.75
    expected_uploaded_filepath = os.path.join(client.application.config['UPLOAD_FOLDER'], f"{job_id}_test_lifecycle.txt")
    assert not os.path.exists(expected_uploaded_filepath), "Uploaded file was not cleaned up"

def test_get_status_invalid_job_id(client):
    response = client.get('/api/analyze/status/invalid-job-id-does-not-exist')
    assert response.status_code == 404

def test_get_results_invalid_job_id(client):
    response = client.get('/api/analyze/results/invalid-job-id-does-not-exist')
    assert response.status_code == 404

def test_get_results_for_pending_job(client, dummy_text_file, mocker):
    # Mock analysis to ensure it stays pending/processing for a bit if needed
    # Patch time.sleep within the mocked function if it's called there, or ensure the side_effect takes time
    def long_running_mock(*args, **kwargs):
        time.sleep(0.5) # Simulate work
        return {"summary":"delayed"}
    mocker.patch('Scripts.api_server.run_text_analysis', side_effect=long_running_mock)

    submit_data = {'analysis_type': 'text', 'data_source_type': 'upload'}
    files = {'text_file': (open(dummy_text_file, 'rb'), 'pending_job_test.txt')}
    submit_response = client.post('/api/analyze', data=submit_data, content_type='multipart/form-data', buffered=True, files=files)
    job_id = submit_response.get_json()['job_id']

    results_response = client.get(f'/api/analyze/results/{job_id}')
    assert results_response.status_code == 422 # Job not yet completed
    
    # Wait for the job to actually complete to allow thread to finish and cleanup
    max_wait_time = 5; start_wait = time.time()
    while time.time() - start_wait < max_wait_time:
        status_resp = client.get(f'/api/analyze/status/{job_id}')
        status_json = status_resp.get_json()
        if status_json['status'] in ['completed', 'failed']:
            if status_json['status'] == 'completed': # Fetch results to trigger cleanup
                 client.get(f'/api/analyze/results/{job_id}')
            break
        time.sleep(0.2)


# --- Fixtures for Mocked Analyzer Results (from test_analysis_logic.py) ---

@pytest.fixture
def mock_text_analysis_result_single_logic(): # Renamed to avoid clash if used in same file
    return {
        "bias_score": 5.0, "diversity_index": 6.5,
        "western_ethics_score": 7.0, "ubuntu_ethics_score": 4.0,
        "confucian_ethics_score": 5.5, "islamic_ethics_score": 3.0,
        "cultural_markers": {"western": 0.5, "african": 0.2},
        "demographic_representation": {"gender_male": 0.6, "age_adult": 0.7},
        "text_metadata": {"word_count": 100}
    }

@pytest.fixture
def mock_image_analysis_result_single_logic(): # Renamed
    return {
        "color_distribution": {"red": 0.3, "blue": 0.7},
        "skin_tone_distribution": {"type_3": 0.8, "type_4": 0.2},
        "gender_representation": {"male": 0.4, "female": 0.6, "estimation_confidence": "low"},
        "age_representation": {"adult": 0.9, "child": 0.1, "estimation_confidence": "low"},
        "cultural_elements": {"western": 0.1, "east_asian": 0.3, "estimation_confidence": "low"},
        "image_metadata": {"width": 100, "height": 100, "filename":"test.jpg"},
        "western_ethics_score": 2.0, "ubuntu_ethics_score": 1.0,
        "confucian_ethics_score": 3.0, "islamic_ethics_score": 0.5,
        "ethics_estimation_confidence": "low (proxy based on cultural elements)",
        "diversity_index": 4.5, "diversity_estimation_confidence": "low"
    }

# --- Tests for run_text_analysis (from test_analysis_logic.py) ---

def test_logic_run_text_analysis_single_string(mock_text_analysis_result_single_logic):
    mock_analyzer_instance = MagicMock()
    mock_result_obj = MagicMock(spec=TextAnalysisResult)
    mock_result_obj.to_dict.return_value = mock_text_analysis_result_single_logic
    mock_analyzer_instance.analyze.return_value = mock_result_obj

    with patch('Scripts.app.TextAnalyzer', return_value=mock_analyzer_instance) as mock_text_analyzer_class:
        result = run_text_analysis("Sample text", ['western'], {"max_tokens": 100})
        mock_text_analyzer_class.assert_called_once()
        mock_analyzer_instance.analyze.assert_called_once_with("Sample text")
        assert result == mock_text_analysis_result_single_logic

def test_logic_run_text_analysis_list_of_strings(mock_text_analysis_result_single_logic):
    mock_analyzer_instance = MagicMock()
    mock_result_obj1 = MagicMock(spec=TextAnalysisResult)
    mock_result_obj1.to_dict.return_value = {**mock_text_analysis_result_single_logic, "text_metadata": {"word_count": 10}}
    mock_result_obj2 = MagicMock(spec=TextAnalysisResult)
    mock_result_obj2.to_dict.return_value = {**mock_text_analysis_result_single_logic, "text_metadata": {"word_count": 20}}
    mock_analyzer_instance.analyze.return_value = [mock_result_obj1, mock_result_obj2]

    with patch('Scripts.app.TextAnalyzer', return_value=mock_analyzer_instance) as mock_text_analyzer_class:
        results_list = run_text_analysis(["Text 1", "Text 2"], [], {})
        assert isinstance(results_list, list)
        assert len(results_list) == 2
        assert results_list[0]["text_metadata"]["word_count"] == 10

def test_logic_run_text_analysis_analyzer_error():
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.analyze.side_effect = ValueError("Logic Test Error")
    with patch('Scripts.app.TextAnalyzer', return_value=mock_analyzer_instance):
        with pytest.raises(RuntimeError, match="Text analysis failed: Logic Test Error"):
            run_text_analysis("Error text", [], {})

# --- Tests for run_image_analysis (from test_analysis_logic.py) ---

def test_logic_run_image_analysis_valid_paths(mock_image_analysis_result_single_logic):
    mock_analyzer_instance = MagicMock()
    mock_result_obj = MagicMock(spec=ImageAnalysisResult)
    mock_result_obj.to_dict.return_value = mock_image_analysis_result_single_logic
    mock_analyzer_instance.batch_process_images.return_value = {"path/img.jpg": mock_result_obj}

    with patch('Scripts.app.ImageAnalyzer', return_value=mock_analyzer_instance) as mock_image_analyzer_class:
        results_dict = run_image_analysis(["path/img.jpg"], "medium", [], 16)
        mock_image_analyzer_class.assert_called_once()
        mock_analyzer_instance.batch_process_images.assert_called_once_with(["path/img.jpg"])
        assert results_dict["path/img.jpg"] == mock_image_analysis_result_single_logic

def test_logic_run_image_analysis_no_paths():
    with patch('Scripts.app.ImageAnalyzer') as mock_image_analyzer_class:
        results = run_image_analysis([], "medium", [], 16)
        assert results == {}
        mock_image_analyzer_class.assert_not_called()

def test_logic_run_image_analysis_analyzer_error():
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.batch_process_images.side_effect = TypeError("Image Logic Error")
    with patch('Scripts.app.ImageAnalyzer', return_value=mock_analyzer_instance):
        with pytest.raises(RuntimeError, match="Image analysis failed: Image Logic Error"):
            run_image_analysis(["path/err.jpg"], "basic", [], 16)

# --- Tests for create_tradition_radar_chart (from test_analysis_logic.py) ---

def test_logic_create_tradition_radar_chart_data_valid():
    data = {"western_ethics_score": 7.5, "ubuntu_ethics_score": 5.0}
    traditions = ["western", "ubuntu", "missing_tradition"]
    result = create_tradition_radar_chart(data, traditions)
    assert result["categories"] == ["Western", "Ubuntu", "Missing_tradition"]
    assert result["series"][0]["data"] == [7.5, 5.0, 0.0]

# --- Tests for create_d3_visualization_data (from test_analysis_logic.py) ---

def test_logic_create_d3_visualization_data_single_item():
    data_input = [{"western_ethics_score": 8, "ubuntu_ethics_score": "6.5"}]
    result = create_d3_visualization_data(data_input, title="D3 Single Logic")
    assert result["average_scores"][0]["average"] == 8.0
    assert result["average_scores"][1]["average"] == 6.5
    assert len(result["raw_items"]) == 1

def test_logic_create_d3_visualization_data_empty_input():
    result = create_d3_visualization_data([], title="D3 Empty Logic")
    assert result["data"] == []
    assert result["message"] == "No data available for visualization."

def test_logic_create_d3_visualization_data_invalid_input_type():
    result = create_d3_visualization_data("not a list", title="D3 Invalid Logic")
    assert result["error"] == "Invalid data type for visualization."

# TODO: Add tests for sample data if implementation is complete
# TODO: Add tests for combined text and image analysis for API
# TODO: Add tests for advanced_options variations in API calls
# TODO: Add more specific error condition tests for API (e.g. advanced_options format)
# TODO: Add more edge case tests for analysis logic functions (e.g. empty strings, lists with Nones)
