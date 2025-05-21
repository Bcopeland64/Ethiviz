import os
import sys
import json
import uuid
import threading
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
from werkzeug.utils import secure_filename

# Ensure the parent directory is in sys.path to allow imports from Scripts
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import necessary components from other modules
# Assuming TextAnalyzer and ImageAnalyzer are self-contained or their dependencies are handled
try:
    from Scripts.text_analyzer import TextAnalyzer
    HAS_TEXT_ANALYZER = True
except ImportError as e:
    logging.warning(f"Could not import TextAnalyzer: {e}. Text analysis endpoints will be affected.")
    HAS_TEXT_ANALYZER = False
    TextAnalyzer = None

try:
    from Scripts.image_analyzer import ImageAnalyzer
    HAS_IMAGE_ANALYZER = True
except ImportError as e:
    logging.warning(f"Could not import ImageAnalyzer: {e}. Image analysis endpoints will be affected.")
    HAS_IMAGE_ANALYZER = False
    ImageAnalyzer = None

# Import refactored analysis runners and data preparers from app.py
# These functions are expected to be decoupled from Streamlit UI
try:
    from Scripts.app import (
        run_text_analysis,
        run_image_analysis,
        create_tradition_radar_chart, # This was the old name, now it returns JSON
        create_d3_visualization_data, # This is the new name for D3 data
        # load_image, # Potentially needed if handling images directly in API beyond just paths
        # safe_mean # Utility, might not be directly used by API layer
    )
    HAS_APP_HELPERS = True
except ImportError as e:
    logging.warning(f"Could not import helper functions from Scripts.app: {e}. API functionality may be limited.")
    HAS_APP_HELPERS = False
    # Define placeholders if import fails to prevent NameErrors later, though endpoints might not work
    run_text_analysis = None
    run_image_analysis = None
    create_tradition_radar_chart = None
    create_d3_visualization_data = None


app = Flask(__name__)
CORS(app) # Enable CORS for all routes and origins. For production, configure specific origins.

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS_TEXT = {'csv', 'xlsx', 'xls', 'json', 'txt'}
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# In-memory job store
jobs = {}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.INFO)

# --- Helper for Standardized Error Responses ---
def make_error_response(message, status_code, details=None):
    response = {"error": message}
    if details:
        response["details"] = details
    app.logger.error(f"Error {status_code}: {message} - Details: {details}")
    return jsonify(response), status_code

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/')
def home():
    return jsonify({"message": "EthiViz API Server is running."})

# --- Sample Data (Placeholder) ---
SAMPLE_DATA_STORE = {
    "texts": [
        {"id": "sample_text_1", "name": "General Ethics Sample", "description": "A collection of sentences touching on various ethical concepts."},
        # {"id": "sample_text_2", "name": "Another Text Sample", "path": "path/to/actual/sample2.csv"} # If loading from file
    ],
    "images": [
        {"id": "sample_image_set_1", "name": "General Iconography", "description": "A diverse set of icons and symbols."},
        # {"id": "sample_image_set_2", "name": "Nature Photos", "path": "path/to/sample_images_nature/"} # If loading from dir
    ]
}
# Actual sample data loading logic will be needed in run_analysis_job or a helper

@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """Returns available sample datasets."""
    return jsonify(SAMPLE_DATA_STORE)

# --- Analysis Job Function ---
def run_analysis_job(job_id, analysis_type, data_inputs, selected_traditions, advanced_options):
    """
    Runs the analysis in a separate thread.
    Updates the job status and results in the global 'jobs' dictionary.
    """
    app.logger.info(f"Starting analysis for job_id: {job_id}")
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["start_time"] = time.time()

    try:
        text_results = None
        image_results = None

        # --- Text Analysis ---
        if "text" in analysis_type.lower():
            if not HAS_TEXT_ANALYZER or not run_text_analysis:
                raise RuntimeError("TextAnalyzer or run_text_analysis function is not available.")
            
            text_input = data_inputs.get("text_input") # This should be List[str] or str (path)
            app.logger.info(f"Job {job_id}: Running text analysis. Input type: {type(text_input)}")

            # The run_text_analysis from app.py expects a list of strings or a single string.
            # If it's a path, TextAnalyzer inside run_text_analysis handles file reading.
            text_results = run_text_analysis(
                text_data_input=text_input,
                traditions=selected_traditions,
                advanced_options=advanced_options.get("text_advanced_options", {})
            )
            app.logger.info(f"Job {job_id}: Text analysis completed.")

        # --- Image Analysis ---
        if "image" in analysis_type.lower():
            if not HAS_IMAGE_ANALYZER or not run_image_analysis:
                raise RuntimeError("ImageAnalyzer or run_image_analysis function is not available.")

            image_paths = data_inputs.get("image_paths") # This should be List[str] (paths to images)
            if not image_paths:
                raise ValueError("Image analysis requested but no image paths provided.")
            app.logger.info(f"Job {job_id}: Running image analysis for {len(image_paths)} images.")

            img_adv_opts = advanced_options.get("image_advanced_options", {})
            feature_level = img_adv_opts.get("feature_level", "medium") # default
            batch_size = img_adv_opts.get("batch_size", 16) # default
            use_pretrained = feature_level == "advanced" # simplified logic for example

            image_results = run_image_analysis(
                image_paths=image_paths,
                feature_level=feature_level,
                traditions=selected_traditions,
                batch_size=batch_size,
                use_pretrained_models=use_pretrained
            )
            app.logger.info(f"Job {job_id}: Image analysis completed.")

        # --- Combine Results ---
        final_results = {}
        if text_results:
            final_results["text_analysis"] = text_results
        if image_results:
            final_results["image_analysis"] = image_results
        
        if not final_results: # Neither analysis ran or produced results
            raise ValueError("No analysis was performed or results were empty.")

        jobs[job_id]["result"] = final_results
        jobs[job_id]["status"] = "completed"
        app.logger.info(f"Job {job_id} completed successfully.")

    except FileNotFoundError as fnf_error:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"File not found: {str(fnf_error)}"
        app.logger.error(f"Job {job_id} failed: File not found - {fnf_error}", exc_info=True)
    except ValueError as val_error:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Invalid input or configuration: {str(val_error)}"
        app.logger.error(f"Job {job_id} failed: Value error - {val_error}", exc_info=True)
    except RuntimeError as rt_error: # Catch errors from analysis modules
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Analysis runtime error: {str(rt_error)}"
        app.logger.error(f"Job {job_id} failed: Runtime error - {rt_error}", exc_info=True)
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        # The following line was missing indentation
        jobs[job_id]["error"] = f"An unexpected error occurred during analysis: {str(e)}"
        # Log the full traceback for unexpected errors
        app.logger.exception(f"Job {job_id} failed with unexpected error: {e}")
    finally:
        jobs[job_id]["end_time"] = time.time()
        jobs[job_id]["duration_seconds"] = jobs[job_id]["end_time"] - jobs[job_id].get("start_time", jobs[job_id]["end_time"])


# --- API Endpoints ---
@app.route('/api/analyze', methods=['POST'])
def submit_analysis():
    """
    Submits a new analysis job.
    Expects multipart/form-data with analysis parameters and optional files.
    """
    app.logger.info(f"Received /api/analyze POST request from {request.remote_addr}")
    try:
        # --- Input Validation ---
        if 'analysis_type' not in request.form:
            return make_error_response("Missing 'analysis_type' parameter.", 400, 
                                       details="Provide 'text', 'image', or 'text_and_image'.")
        
        analysis_type = request.form['analysis_type'].lower()
        valid_analysis_types = ['text', 'image', 'text_and_image']
        if analysis_type not in valid_analysis_types:
            return make_error_response(f"Invalid 'analysis_type': {analysis_type}.", 400,
                                       details=f"Valid types are: {', '.join(valid_analysis_types)}.")

        data_source_type = request.form.get('data_source_type', 'upload').lower()
        valid_data_source_types = ['upload', 'sample']
        if data_source_type not in valid_data_source_types:
            return make_error_response(f"Invalid 'data_source_type': {data_source_type}.", 400,
                                       details=f"Valid types are: {', '.join(valid_data_source_types)}.")

        selected_traditions = request.form.getlist('selected_traditions')
        if not selected_traditions: # Default if empty, or enforce if needed
            selected_traditions = ['western', 'ubuntu', 'confucian', 'islamic'] 
            app.logger.info("No traditions selected, using default list.")
        elif not isinstance(selected_traditions, list) or not all(isinstance(t, str) for t in selected_traditions):
             return make_error_response("'selected_traditions' must be a list of strings.", 400)


        advanced_options_json = request.form.get('advanced_options', '{}')
        try:
            advanced_options = json.loads(advanced_options_json)
            if not isinstance(advanced_options, dict):
                raise ValueError("Advanced options should be a JSON object.")
        except (json.JSONDecodeError, ValueError) as e:
            return make_error_response("Invalid JSON format for 'advanced_options'.", 400, details=str(e))

        job_id = str(uuid.uuid4())
        data_inputs = {"source_type": data_source_type}
        
        # --- File/Sample Data Handling with Validation ---
        if data_source_type == 'upload':
            # Text analysis file handling
            if analysis_type in ['text', 'text_and_image']:
                if 'text_file' not in request.files:
                    return make_error_response("Missing 'text_file' for text analysis upload.", 400)
                text_file = request.files['text_file']
                if text_file.filename == '':
                    return make_error_response("No text file selected for upload.", 400)
                if not allowed_file(text_file.filename, ALLOWED_EXTENSIONS_TEXT):
                    return make_error_response(f"Invalid text file type: {text_file.filename}.", 400,
                                               details=f"Allowed text types: {', '.join(ALLOWED_EXTENSIONS_TEXT)}")
                text_filename = secure_filename(text_file.filename)
                text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{text_filename}")
                text_file.save(text_filepath)
                data_inputs["text_input"] = text_filepath
                app.logger.info(f"Saved text file for job {job_id} to {text_filepath}")

            # Image analysis file handling
            if analysis_type in ['image', 'text_and_image']:
                image_files = request.files.getlist('image_files')
                if not image_files or all(f.filename == '' for f in image_files):
                    return make_error_response("Missing 'image_files' for image analysis upload.", 400)
                
                saved_image_paths = []
                for img_file in image_files:
                    if not allowed_file(img_file.filename, ALLOWED_EXTENSIONS_IMAGE):
                        # Clean up any partially saved files for this job before returning error
                        for p in saved_image_paths: os.remove(p)
                        if "text_input" in data_inputs and os.path.exists(data_inputs["text_input"]): os.remove(data_inputs["text_input"])
                        return make_error_response(f"Invalid image file type: {img_file.filename}.", 400,
                                                   details=f"Allowed image types: {', '.join(ALLOWED_EXTENSIONS_IMAGE)}")
                    img_filename = secure_filename(img_file.filename)
                    img_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{img_filename}")
                    img_file.save(img_filepath)
                    saved_image_paths.append(img_filepath)
                data_inputs["image_paths"] = saved_image_paths
                app.logger.info(f"Saved {len(saved_image_paths)} image files for job {job_id}.")
        
        elif data_source_type == 'sample':
            if analysis_type in ['text', 'text_and_image']:
                sample_text_id = request.form.get('sample_text_id')
                if not sample_text_id:
                    return make_error_response("Missing 'sample_text_id' for sample text analysis.", 400)
                # TODO: Implement actual sample data loading based on ID
                if sample_text_id == "sample_text_1": # Placeholder
                     data_inputs["text_input"] = "This is sample text about individual rights and community harmony. Ubuntu teaches us compassion. Confucianism values order. Islamic ethics stress justice."
                     app.logger.info(f"Using sample text ID: {sample_text_id} for job {job_id}")
                else:
                     return make_error_response(f"Sample text ID '{sample_text_id}' not recognized.", 404)
            
            if analysis_type in ['image', 'text_and_image']:
                sample_image_id = request.form.get('sample_image_id')
                if not sample_image_id:
                     return make_error_response("Missing 'sample_image_id' for sample image analysis.", 400)
                # TODO: Implement actual sample image path retrieval
                app.logger.warning(f"Sample image data handling for ID '{sample_image_id}' is not fully implemented. Job {job_id} may fail if it relies on this.")
                # For now, let this pass but it will likely fail in run_analysis_job if image_paths isn't populated
                data_inputs["image_paths"] = [] # Placeholder; needs actual paths
                if not data_inputs["image_paths"]: # If still no paths after sample logic
                    return make_error_response("Sample image data handling not implemented or ID not found.", 501,
                                               details=f"Sample image ID '{sample_image_id}' could not be processed.")
                app.logger.info(f"Using sample image ID: {sample_image_id} for job {job_id}")

        # --- Store Job and Start Thread ---
        jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "analysis_type": analysis_type,
            "data_inputs_summary": {k: (v if k != "image_paths" else f"{len(v)} images") for k,v in data_inputs.items()},
            "selected_traditions": selected_traditions,
            "advanced_options": advanced_options,
            "submission_time": time.time()
        }
        
        app.logger.info(f"Job {job_id} created. Initial status: pending. Starting analysis thread.")
        thread = threading.Thread(target=run_analysis_job, args=(
            job_id,
            analysis_type,
            data_inputs,
            selected_traditions,
            advanced_options
        ))
        thread.daemon = True
        thread.start()

        status_url = request.url_root + f"api/analyze/status/{job_id}"
        return jsonify({
            "message": "Analysis job submitted successfully.",
            "job_id": job_id,
            "status": "pending",
            "status_url": status_url
        }), 202

    except Exception as e:
        # Catch-all for unexpected errors during request processing
        app.logger.exception(f"Unexpected error in /api/analyze: {e}")
        return make_error_response("An unexpected server error occurred while submitting the job.", 500, details=str(e))


@app.route('/api/analyze/status/<job_id>', methods=['GET'])
def get_analysis_status(job_id):
    """Returns the status of an analysis job."""
    job = jobs.get(job_id)
    if not job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "submission_time": job.get("submission_time"),
        "start_time": job.get("start_time"),
        "end_time": job.get("end_time"),
        "duration_seconds": job.get("duration_seconds")
    }
    if job["status"] == "completed":
        response["message"] = "Analysis completed successfully."
        response["results_url"] = request.url_root + f"api/analyze/results/{job_id}"
    elif job["status"] == "failed":
        response["error_message"] = job.get("error", "An unknown error occurred during analysis.")
        response["details"] = job.get("error_details") # Optional more specific details
    elif job["status"] == "processing":
        response["message"] = "Analysis is currently in progress."
    elif job["status"] == "pending":
        response["message"] = "Analysis job is pending execution."
        
    return jsonify(response)

@app.route('/api/analyze/results/<job_id>', methods=['GET'])
def get_analysis_results(job_id):
    """Returns the results of a completed analysis job."""
    job = jobs.get(job_id)
    if not job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")
    if job["status"] != "completed":
        return make_error_response("Job not yet completed or has failed.", 422, # Unprocessable Entity
                                   details=f"Current job status: {job['status']}. Error: {job.get('error')}")
    
    # Optional: Clean up uploaded files (consider moving to a separate cleanup mechanism for production)
    data_inputs_summary = job.get("data_inputs_summary", {})
    if data_inputs_summary.get("source_type") == "upload":
        text_file_path = job.get("data_inputs", {}).get("text_input")
        if text_file_path and os.path.exists(text_file_path):
            try:
                os.remove(text_file_path)
                app.logger.info(f"Cleaned up text file: {text_file_path}")
            except Exception as e_clean:
                app.logger.error(f"Error cleaning text file {text_file_path}: {e_clean}")

        image_file_paths = job.get("data_inputs", {}).get("image_paths", [])
        for p in image_file_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    app.logger.info(f"Cleaned up image file: {p}")
                except Exception as e_clean:
                    app.logger.error(f"Error cleaning image file {p}: {e_clean}")
                
    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "analysis_type": job.get("analysis_type"),
        "results": job.get("result")
    })
# Lines from 414 to 483 (original numbering) containing the
# erroneous 'if __name__ == "__main__":' block and duplicated routes
# have been removed.
# The code now transitions to the correct 'if __name__ == "__main__":' block.


if __name__ == '__main__':
    app.logger.info(f"EthiViz API Server starting...")
    app.logger.info(f"TextAnalyzer available: {HAS_TEXT_ANALYZER}")
    app.logger.info(f"ImageAnalyzer available: {HAS_IMAGE_ANALYZER}")
    app.logger.info(f"App helpers available: {HAS_APP_HELPERS}")
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    # Use a different port if 5000 is common, e.g., 5001 for the API server
    app.run(debug=True, host='0.0.0.0', port=5001)
