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

### Streamlit Interface

The easiest way to use EthiViz is through its interactive Streamlit interface:

```bash
# Launch the Streamlit app 
python run.py
# Or directly with streamlit
streamlit run app.py
```

This opens a web interface where you can:
- Upload text data (CSV, Excel) and images
- Use included sample text data with multiple ethical traditions 
- Use included sample images for demonstration
- Select ethical traditions to include in the analysis
- Configure advanced settings like feature extraction level
- Run analyses and view interactive results
- Save results to a specified output directory

### Command Line Interface

For batch processing or integration with other tools:

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