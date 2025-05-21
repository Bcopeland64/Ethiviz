# EthiViz - Cultural Bias Analysis Platform

EthiViz is a comprehensive platform for analyzing cultural bias in both text and image data through multiple ethical traditions, including Western, Ubuntu, Confucian, and Islamic perspectives.

## Features

- **Multi-tradition Ethical Analysis**: Analyze data through different cultural and ethical frameworks
- **Text & Image Analysis**: Process both textual and visual content for bias detection
- **Lightweight Image Processing**: Tiered feature extraction approach for computational efficiency
- **Interactive Visualizations**: Rich, interactive dashboards using D3.js and Plotly
- **Diversity Metrics**: Shannon entropy-based diversity calculations across multiple dimensions
- **Batch Processing**: Efficient processing of multiple images and text samples
- **Graceful Dependency Management**: Works with minimal dependencies but leverages advanced libraries when available
- **Streamlit UI**: Modern, sleek dark-themed user interface for intuitive analysis

## Installation

### Using the Setup Scripts (Recommended)

#### On Linux/macOS:
```bash
# Clone the repository
git clone https://github.com/yourusername/ethiviz.git
cd ethiviz

# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh

# Activate the virtual environment
source activate-ethiviz.sh

# Run the application
streamlit run app.py
```

#### On Windows:
```bash
# Clone the repository
git clone https://github.com/yourusername/ethiviz.git
cd ethiviz

# Run the setup script
setup.bat

# Activate the virtual environment
activate-ethiviz.bat

# Run the application
streamlit run app.py
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ethiviz.git
cd ethiviz

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required for text analysis)
python -m spacy download en_core_web_md
```

## Usage

EthiViz can be run in different modes: as a Streamlit application (original UI), or as a decoupled frontend/backend application.

### Mode 1: Streamlit Interface (Original)

The easiest way to use EthiViz's original UI is through its interactive Streamlit interface:

```bash
# Ensure you are in the root directory of the project
# Activate your Python virtual environment if you created one
# e.g., source venv/bin/activate or venv\Scripts\activate.bat

# Launch the Streamlit app 
python Scripts/run.py 
# Or directly with streamlit:
# streamlit run Scripts/app.py
```

This opens a web interface (usually on port 8501) where you can:
- Upload text data (CSV, Excel) and images
- Use included sample text data
- Use included sample images
- Select ethical traditions for analysis
- Configure advanced settings
- Run analyses and view interactive results
- Save results.

### Mode 2: Decoupled Frontend (React) and Backend (Flask API)

This mode allows for a more modern web application experience. The backend API server handles analysis requests, and the React frontend provides the user interface.

**1. Running the Backend API Server (Flask):**

```bash
# Ensure you are in the root directory of the project
# Activate your Python virtual environment
# e.g., source venv/bin/activate or venv\Scripts\activate.bat

# Install/update Python dependencies
pip install -r requirements.txt

# Run the Flask API server
python Scripts/api_server.py
```
The Flask API server will typically start on `http://localhost:5001`. Check the console output for the exact URL.

**2. Running the Frontend Application (React):**

```bash
# Open a new terminal window or tab
# Navigate to the frontend project directory
cd project

# Install frontend dependencies (if you haven't already)
npm install

# Start the React development server
npm run dev
```
The React frontend will typically start on `http://localhost:5173` (Vite default) or `http://localhost:3000` (Create React App default). Check your console output.

**Important:**
- Both the backend API server and the frontend application must be running concurrently to use the decoupled mode.
- Ensure the API base URL in the frontend matches the URL where your Flask API server is running. This is typically defined as `API_BASE_URL` in `project/src/components/ConfigPanel.tsx` (default `http://localhost:5001`).
- The Flask server has CORS enabled for `http://localhost:5173` (common Vite default). If your React app runs on a different port, you might need to adjust the CORS configuration in `Scripts/api_server.py` for production.

Once both are running, open the frontend URL (e.g., `http://localhost:5173`) in your browser to use the application.

**API Endpoint Summary (Decoupled Mode):**

The Flask backend exposes the following main API endpoints:

*   `POST /api/analyze`: Submits data (text or image files) for analysis. Expects `multipart/form-data` with parameters like `analysis_type`, `data_source_type`, `selected_traditions`, and files. Returns a job ID and status URL.
*   `GET /api/analyze/status/{job_id}`: Checks the status of an ongoing or completed analysis job.
*   `GET /api/analyze/results/{job_id}`: Retrieves the full analysis results for a completed job.
*   `GET /api/sample-data`: Lists available sample datasets that can be used (currently placeholder, full functionality for loading these samples in backend is pending).
*   `GET /`: A simple health check endpoint for the API server.

For detailed request/response formats, refer to the implementation in `Scripts/api_server.py`.

### Command Line Interface (for batch processing via original run.py)

For batch processing or integration with other tools using the original script:

```bash
# Analyze text data
python run.py --text-data path/to/textdata.csv

# Analyze images
python run.py --image-dir path/to/image/directory

# Analyze both text and images
python run.py --text-data path/to/textdata.csv --image-dir path/to/image/directory

# Specify ethical traditions to use
python run.py --text-data path/to/textdata.csv --traditions western,ubuntu,confucian,islamic

# Set image analysis feature extraction level
python run.py --image-dir path/to/image/directory --feature-level medium

# Specify output directory and dashboard port
python run.py --text-data path/to/textdata.csv --output-dir ./my_results --port 8080
```

### Python API

For programmatic use and custom applications:

```python
from text_analyzer import TextAnalyzer
from image_analyzer import ImageAnalyzer
from visualization import create_dashboard

# Text analysis
text_analyzer = TextAnalyzer(traditions=['western', 'ubuntu', 'confucian', 'islamic'])
text_results = text_analyzer.analyze('path/to/data.csv')

# Image analysis
image_analyzer = ImageAnalyzer(feature_level='medium')
image_paths = ['path/to/image1.jpg', 'path/to/image2.jpg']
image_results = image_analyzer.analyze_batch(image_paths)

# Create dashboard
create_dashboard(text_results=text_results, image_results=image_results, port=8050)
```

## Ethical Traditions

EthiViz analyzes data through multiple ethical traditions:

1. **Western Ethics**: Based on principles like autonomy, beneficence, non-maleficence, and justice
2. **Ubuntu Ethics**: "I am because we are" - focuses on community, relationality, and shared humanity
3. **Confucian Ethics**: Emphasizes harmony, proper relationships, and virtues like benevolence and reciprocity
4. **Islamic Ethics**: Balances individual and community rights, emphasizing justice, fairness, and human dignity

## Image Analysis

The image analysis functionality includes:

- **Skin Tone Analysis**: Fitzpatrick scale approximation to analyze representation diversity
- **Feature Extraction**: Tiered approach with color histograms, HOG features, and deep learning
- **Diversity Calculations**: Shannon entropy-based metrics for skin tone, gender, age distribution
- **Cultural Element Detection**: Identification of cultural signifiers and their distribution

## Visualizations

The platform provides rich interactive visualizations:

- **Metric Cards**: At-a-glance summary of key metrics
- **Comparative Charts**: Compare scores across ethical traditions
- **Demographic Analysis**: Visualize demographic distributions in images
- **Radar Charts**: Multi-dimensional ethical analysis
- **Image Gallery**: View analyzed images with their metrics
- **Combined Analysis**: Compare text and image results

## Requirements

- Python 3.8+
- NumPy, Pandas, SciPy
- Streamlit, Plotly (for visualization)
- Pillow (required for basic image processing)
- OpenCV (optional - enables medium-level feature extraction)
- TensorFlow (optional - enables advanced feature extraction)
- SpaCy (with at least en_core_web_md model)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
