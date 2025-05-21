# EthiViz - Cultural Bias Analysis Platform (React + Flask Edition)

EthiViz is a comprehensive platform for analyzing cultural bias in both text and image data. It leverages multiple ethical traditions, including Western, Ubuntu, Confucian, and Islamic perspectives, to provide a nuanced understanding of potential biases. This version of EthiViz features a decoupled architecture with a React frontend and a Flask (Python) backend API.

## Overview

The platform allows users to upload text or image data, which is then processed by the backend API. The analysis results, including bias scores, diversity metrics, and ethical alignment scores, are then presented in an interactive web interface powered by React.

## Features

- **Decoupled Architecture**: Modern React frontend with a robust Flask backend API for analysis.
- **Asynchronous Job Processing**: Handles potentially long-running analyses without blocking the UI.
- **Multi-tradition Ethical Analysis**: Analyze data through Western, Ubuntu, Confucian, and Islamic ethical frameworks.
- **Text & Image Analysis**: Process both textual (CSV, TXT, JSON, XLSX) and visual content (JPG, PNG, WEBP, GIF).
- **Bias and Diversity Metrics**: Calculates various scores including bias, diversity index, and alignment with different ethical traditions.
- **Lightweight Image Processing**: Tiered feature extraction for images, balancing efficiency and detail.
- **Interactive Frontend**: (Future Goal) Rich, interactive dashboards and visualizations for exploring results. Currently displays raw JSON and basic summaries.
- **API for Programmatic Access**: The backend API can be used by other services or for batch processing.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python**: Version 3.8+ (for the backend API server). Includes `pip` for package management.
- **Node.js**: Version 16.x or higher (for the React frontend). Includes `npm` for package management.
- **Git**: For cloning the repository.

## Installation

Follow these steps to set up the EthiViz platform:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/ethiviz.git # Replace with actual repo URL
    cd ethiviz
    ```

2.  **Backend Setup (Flask API):**
    *   Navigate to the project root directory (`ethiviz`).
    *   Create and activate a Python virtual environment (recommended):
        ```bash
        python -m venv venv
        # On macOS/Linux:
        source venv/bin/activate
        # On Windows:
        # venv\Scripts\activate.bat
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Download the spaCy model (required for text analysis):
        ```bash
        python -m spacy download en_core_web_sm 
        # Or en_core_web_md for potentially better accuracy but larger size
        ```

3.  **Frontend Setup (React App):**
    *   Navigate to the frontend project directory:
        ```bash
        cd project 
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```
    *   Return to the project root directory:
        ```bash
        cd ..
        ```

## Running the Application

To use EthiViz, both the backend API server and the frontend React application must be running concurrently.

**1. Start the Backend API Server (Flask):**
   *   Ensure you are in the project root directory (`ethiviz`).
   *   Activate your Python virtual environment if you haven't already.
   *   Run the Flask API server:
    ```bash
    python Scripts/api_server.py
    ```
   The API server will typically start on `http://localhost:5001`. Check the console output for the exact URL.

**2. Start the Frontend Application (React):**
   *   Open a **new terminal window or tab**.
   *   Navigate to the frontend project directory:
    ```bash
    cd project
    ```
   *   Start the React development server:
    ```bash
    npm run dev
    ```
   The React frontend will typically start on `http://localhost:5173` (Vite default). Check the console output for the exact URL.

**3. Access EthiViz:**
   Once both servers are running, open the frontend URL (e.g., `http://localhost:5173`) in your web browser.

**Important Notes:**
- **Concurrent Execution**: Both servers must remain running.
- **API URL Configuration**: The React frontend is configured to connect to the API server at `http://localhost:5001`. If your API server runs on a different port, update the `API_BASE_URL` constant in `project/src/components/ConfigPanel.tsx`.
- **CORS**: The Flask server is configured with `Flask-CORS` to allow requests from `http://localhost:5173` (common Vite default). If your React app runs on a different port, you may need to adjust the CORS settings in `Scripts/api_server.py` for production environments.

## API Details

The Flask backend provides a RESTful API for analysis tasks. Key endpoints include:

*   `POST /api/analyze`: Submits data (text or image files) for analysis.
    *   Expects `multipart/form-data`.
    *   Key form fields: `analysis_type` ('text', 'image', 'text_and_image'), `data_source_type` ('upload', 'sample'), `selected_traditions` (list), `advanced_options` (JSON string).
    *   File fields: `text_file` (if `analysis_type` includes 'text' and `data_source_type` is 'upload'), `image_files` (if `analysis_type` includes 'image' and `data_source_type` is 'upload').
    *   Returns: `202 Accepted` with a `job_id` and `status_url`.
*   `GET /api/analyze/status/{job_id}`: Checks the status of an analysis job (`pending`, `processing`, `completed`, `failed`).
*   `GET /api/analyze/results/{job_id}`: Retrieves the results for a completed job.
*   `GET /api/sample-data`: Lists available sample datasets (Note: full sample data loading functionality in the backend is currently a placeholder).
*   `GET /`: Health check for the API server.

For more detailed information on request/response formats, refer to the source code in `Scripts/api_server.py`.

## Core Analysis Capabilities

- **Ethical Traditions**: Analyzes data through Western, Ubuntu, Confucian, and Islamic ethical lenses.
- **Image Analysis Features**: Includes skin tone analysis (Fitzpatrick scale approximation), tiered feature extraction (color histograms, HOG, deep learning), diversity calculations (Shannon entropy), and basic cultural element detection.
- **Text Analysis Features**: Utilizes NLP techniques (via spaCy/NLTK) for tokenization, sentiment analysis (if transformers are available), and identification of keywords related to ethical frameworks and cultural markers.

## Visualizations (React Frontend)

The React frontend currently displays:
- Raw JSON output of analysis results.
- Basic summaries of text and image analysis (e.g., bias score, diversity index, number of images).
- Placeholders for future integration of more detailed charts and interactive visualizations.

(The original Streamlit application contained more mature visualizations like radar charts, demographic distributions, etc. These are planned for re-implementation or new implementation in the React frontend.)

## Legacy Streamlit Interface

This project also contains an older Streamlit-based interface which offers a different user experience and a more developed set of visualizations. For instructions on how to set up and run the Streamlit version, please see [STREAMLIT_GUIDE.md](./STREAMLIT_GUIDE.md).

## Requirements Overview

- **Backend**: Python 3.8+, Flask, Flask-CORS, spaCy, NLTK, Pillow. Optional: OpenCV, TensorFlow for advanced image features. (See `requirements.txt` for full list).
- **Frontend**: Node.js, React, Vite, Axios, Tailwind CSS. (See `project/package.json` for full list).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Ensure your contributions align with the project's goals and coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
