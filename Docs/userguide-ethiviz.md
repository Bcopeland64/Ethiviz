# EthiViz User Guide (React + Flask Edition)

Welcome to EthiViz! This guide will help you use the EthiViz platform, featuring a React-based user interface and a Flask backend API, to analyze cultural bias in text and image data.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Getting Started](#getting-started)
3.  [Using the EthiViz Dashboard (React UI)](#using-the-ethiviz-dashboard-react-ui)
    *   [Dashboard Overview](#dashboard-overview)
    *   [Step 1: Select Analysis Type](#step-1-select-analysis-type)
    *   [Step 2: Provide Your Data](#step-2-provide-your-data)
    *   [Step 3: Configure Analysis](#step-3-configure-analysis)
    *   [Step 4: Run Analysis](#step-4-run-analysis)
    *   [Monitoring Job Status](#monitoring-job-status)
4.  [Viewing and Interpreting Results](#viewing-and-interpreting-results)
    *   [Current Results Display](#current-results-display)
    *   [Understanding the JSON Output](#understanding-the-json-output)
    *   [Future Visualizations](#future-visualizations)
5.  [API Usage (Brief Overview)](#api-usage-brief-overview)
6.  [Troubleshooting](#troubleshooting)
7.  [Legacy Streamlit Interface](#legacy-streamlit-interface)

## 1. Introduction

EthiViz is a platform designed to help users identify and understand potential cultural biases in their data. It analyzes content through multiple ethical lenses: Western, Ubuntu, Confucian, and Islamic traditions. This version utilizes a modern web application structure with a React frontend for user interaction and a Flask backend API for processing analysis jobs.

## 2. Getting Started

Before using EthiViz, you need to set up and run both the backend API server and the frontend React application.

*   **Installation**: Please refer to the main [README.md](../README.md) for detailed installation instructions, including prerequisites (Python, Node.js) and steps to set up the backend and frontend environments.
*   **Running the Application**:
    1.  Start the **Backend API Server** (Flask) as described in `README.md` (typically `python Scripts/api_server.py`).
    2.  Start the **Frontend Application** (React) in a separate terminal as described in `README.md` (typically `cd project && npm run dev`).
    3.  Once both servers are running, open the frontend URL (usually `http://localhost:5173`) in your web browser.

## 3. Using the EthiViz Dashboard (React UI)

The EthiViz dashboard allows you to configure and run your analyses.

### Dashboard Overview

The interface primarily consists of:

*   **Configuration Panel (Sidebar)**: On the left (can be toggled), where you set up your analysis parameters, upload data, and start the analysis.
*   **Main Content Area**: On the right, where analysis results, loading messages, or errors are displayed.

### Step 1: Select Analysis Type

In the Configuration Panel:
*   Locate the "Analysis Type" section.
*   Choose between:
    *   **Text**: For analyzing textual data.
    *   **Image**: For analyzing image data.
    *   You can also select "Analyze Text & Image Together?" if you have selected either Text or Image first, to perform a combined analysis.

### Step 2: Provide Your Data

Under the "Data Source" section:

*   **Upload Your Data**:
    1.  Select "Upload Your Data".
    2.  A file upload area will appear.
    3.  **For Text Analysis**: Click "browse files" or drag and drop your text file (e.g., CSV, TXT, XLSX, JSON) into the designated area. The selected file name and size will appear.
        *   Ensure your text file (if CSV/XLSX) contains a column named "text" for the content to be analyzed.
    4.  **For Image Analysis**: Click "browse files" or drag and drop your image files (e.g., JPG, PNG, WEBP) into the area. You can select multiple image files. Selected image names and sizes will be listed.
    5.  **For Text & Image Analysis**: Provide both text and image files as described above.
*   **Use Sample Data**:
    1.  Select "Use Sample Data".
    2.  **(Note: UI for selecting specific sample datasets is currently a work-in-progress in the React frontend. The backend has placeholder logic for `sample_text_1`. Image sample selection is not yet implemented in the UI-backend flow).**
        *   If you select "Text" or "Text & Image" analysis with "Sample Data", it will attempt to use a predefined sample text if the backend supports the default ID (`sample_text_1`).

### Step 3: Configure Analysis

*   **Ethical Traditions**:
    *   In the "Traditions" section, select the ethical frameworks (Western, Ubuntu, Confucian, Islamic) you want to include in the analysis. By default, all are selected. Click to toggle selection.
*   **Advanced Options**:
    *   Expand the "Advanced Options" section to view current analysis parameters (e.g., max tokens for text, feature level for images).
    *   **(Note: The UI to modify these advanced options directly in the React frontend is currently a placeholder. The API uses default values or values set in `ConfigPanel.tsx`'s initial state if not modified via API directly).**

### Step 4: Run Analysis

*   Once you have configured your analysis type, data, and traditions, click the **"Run Analysis"** button at the bottom of the Configuration Panel.
*   The button will be disabled if required inputs are missing (e.g., no analysis type selected, or no file uploaded when "Upload Your Data" is chosen).

### Monitoring Job Status

*   After clicking "Run Analysis":
    *   The button will show a loading state (e.g., "Analyzing...").
    *   A "Job Submitted: <job_id_prefix>..." message will appear in the Configuration Panel, indicating the unique ID for your analysis job.
    *   The Main Content area will display a loading indicator: "Analysis in progress...".
*   The application polls the backend API to check the job status. You might see status updates like "pending" or "processing" in the ConfigPanel if implemented, or simply wait for the main content area to update.

## 4. Viewing and Interpreting Results

### Current Results Display

Once the analysis is complete, the Main Content area will update to show "Analysis Results":

*   **Summaries (Placeholders)**:
    *   If text analysis was performed, a "Text Analysis" section will show basic metrics like "Bias Score" and "Diversity Index". If multiple text items were processed (e.g., from a CSV), it might list these metrics for each item.
    *   If image analysis was performed, an "Image Analysis" section will show the number of images processed and may list basic metrics (like "Diversity Index") for a few sample images.
*   **Raw JSON Output**:
    *   A key part of the current results display is the "Raw JSON Output". This section shows the complete, detailed results from the backend API in a structured JSON format. This is the primary way to access all analyzed metrics currently.

### Understanding the JSON Output

The JSON output will typically have a structure like:

```json
{
  "text_analysis": { // If text analysis was run
    "bias_score": 5.0,
    "diversity_index": 6.5,
    "western_ethics_score": 7.0,
    // ... other text metrics and metadata ...
  },
  "image_analysis": { // If image analysis was run
    "path/to/your/image1.jpg": {
      "diversity_index": 4.5,
      "western_ethics_score": 2.0,
      // ... other image metrics and metadata for image1 ...
    },
    "path/to/your/image2.png": {
      // ... metrics for image2 ...
    }
  }
}
```
*   `text_analysis`: Contains scores and data related to the text analysis. If the input was a single text or file with one text, this will be an object. If it was a file with multiple texts, this might be an array of objects.
*   `image_analysis`: Contains a dictionary where keys are image filenames (or paths as processed by the backend) and values are objects containing the analysis for each image.
*   Refer to the main `README.md` or `STREAMLIT_GUIDE.md` for more details on interpreting specific scores like bias, diversity, and ethical alignment scores, as the underlying metrics are the same.

### Future Visualizations

The React frontend is planned to include more sophisticated and interactive visualizations (e.g., radar charts, bar charts, demographic distributions) based on the JSON data. Currently, these are not yet implemented in the React UI. The JSON output provides the data that will feed these future charts.

## 5. API Usage (Brief Overview)

The EthiViz backend provides a RESTful API that the React frontend uses. Advanced users or developers can also interact with this API directly. Key endpoints include:

*   `POST /api/analyze`: Submit analysis jobs.
*   `GET /api/analyze/status/{job_id}`: Check job status.
*   `GET /api/analyze/results/{job_id}`: Get job results.
*   `GET /api/sample-data`: List available sample data (currently placeholder).

Refer to the "API Details" section in the main `README.md` for more information.

## 6. Troubleshooting

*   **"Failed to fetch", "Network Error", or API errors in ConfigPanel/MainContent**:
    *   Ensure the Flask API backend server is running (execute `python Scripts/api_server.py`).
    *   Verify the `API_BASE_URL` in `project/src/components/ConfigPanel.tsx` (default `http://localhost:5001`) matches where your API server is running.
    *   Check your browser's developer console (usually F12) for more detailed error messages or CORS issues.
*   **"Analysis Failed" message in MainContent**:
    *   This indicates an error during the backend processing. The message might provide details. Check the Flask API server's console output for more detailed logs and Python tracebacks.
*   **File Upload Issues**:
    *   Ensure your files meet the allowed types (e.g., CSV, TXT for text; JPG, PNG for images).
    *   For CSV/Excel text uploads, ensure there is a column named "text".
*   **Analysis Timeout**:
    *   If an analysis job takes too long, the frontend might time out its polling. The job may still be running on the server. You can check the server logs. For very large datasets, consider using the API programmatically or the legacy command-line interface if available.

## 7. Legacy Streamlit Interface

This project also contains an older Streamlit-based interface which offers a different user experience and a more developed set of visualizations. For instructions on how to set up and run the Streamlit version, please see [STREAMLIT_GUIDE.md](./STREAMLIT_GUIDE.md).

---
