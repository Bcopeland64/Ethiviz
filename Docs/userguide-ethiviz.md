# EthiViz User Guide

Welcome to EthiViz, a comprehensive platform for analyzing cultural bias in both text and image data through multiple ethical traditions. This guide will help you navigate the platform's features and functionalities.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Command Line Usage](#command-line-usage)
3. [Python API Usage](#python-api-usage)
4. [Using the Interactive Dashboard](#using-the-interactive-dashboard)
5. [Text Analysis](#text-analysis)
6. [Image Analysis](#image-analysis)
7. [Interpreting Results](#interpreting-results)
8. [Advanced Configurations](#advanced-configurations)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Ensure you have Python 3.8 or higher installed.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

For optimal performance with image analysis, we recommend installing the optional dependencies:

```bash
pip install opencv-python tensorflow
```

### Basic Usage

To run a basic analysis with default settings:

```bash
python run.py --text-data path/to/textdata.csv --image-dir path/to/image/directory
```

## Command Line Usage

EthiViz provides a flexible command-line interface with numerous options:

```bash
python run.py [options]
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--text-data` | Path to text dataset (CSV, JSON, or Excel) | None |
| `--image-dir` | Path to directory containing images | None |
| `--traditions` | Comma-separated list of ethical traditions | western,ubuntu,confucian,islamic |
| `--feature-level` | Feature extraction level for image analysis | medium |
| `--batch-size` | Batch size for processing images | 32 |
| `--output-dir` | Directory to save analysis results | ./results |
| `--port` | Port for the visualization dashboard | 8050 |
| `--no-dashboard` | Skip launching the dashboard | False |

### Examples

Analyze text data only:
```bash
python run.py --text-data data/articles.csv
```

Analyze images only with basic feature extraction:
```bash
python run.py --image-dir data/marketing_images --feature-level basic
```

Analyze both with specific ethical traditions:
```bash
python run.py --text-data data/social_media.csv --image-dir data/profile_pictures --traditions western,ubuntu
```

Save results to a custom directory:
```bash
python run.py --text-data data/survey.csv --output-dir ./my_analysis_results
```

Run analysis without launching the dashboard:
```bash
python run.py --text-data data/comments.csv --no-dashboard
```

## Python API Usage

For programmatic integration or custom workflows, you can use the Python API:

```python
from text_analyzer import TextAnalyzer
from image_analyzer import ImageAnalyzer
from visualization import create_dashboard

# Text analysis
text_analyzer = TextAnalyzer(traditions=['western', 'ubuntu', 'confucian', 'islamic'])
text_results = text_analyzer.analyze('path/to/data.csv')

# Image analysis
image_analyzer = ImageAnalyzer(feature_level='medium', batch_size=32)
image_paths = ['path/to/image1.jpg', 'path/to/image2.jpg']
image_results = image_analyzer.analyze_batch(image_paths)

# Create dashboard
create_dashboard(text_results=text_results, image_results=image_results, port=8050)
```

### Customizing Text Analysis

```python
analyzer = TextAnalyzer(
    traditions=['western', 'ubuntu'],  # Only use Western and Ubuntu traditions
    nlp_model='en_core_web_md',        # Specify SpaCy model
    max_tokens=10000                    # Limit token count for performance
)
```

### Customizing Image Analysis

```python
analyzer = ImageAnalyzer(
    feature_level='advanced',           # Use deep learning features
    traditions=['confucian', 'islamic'], # Only use Confucian and Islamic traditions
    batch_size=64,                      # Process 64 images at once
    detect_demographics=True,           # Enable demographic detection
    detect_cultural_elements=True       # Enable cultural element detection
)

# Analyze a single image
result = analyzer.analyze_image('path/to/image.jpg')

# Access specific metrics
skin_tone_diversity = result['skin_tone_diversity']
confucian_ethics_score = result['confucian_ethics_score']
```

## Using the Interactive Dashboard

The interactive dashboard provides comprehensive visualizations of analysis results.

### Dashboard Layout

The dashboard is organized into three main tabs:

1. **Text Analysis**: Visualizations for text data
2. **Image Analysis**: Visualizations for image data
3. **Combined Analysis**: Comparative visualizations between text and image results

### Navigating Visualizations

- **Hover** over data points for detailed information
- Use the **toolbar** in the upper right of each chart for interactions:
  - Pan: Move around the visualization
  - Box Select: Select data points
  - Zoom: Zoom in/out
  - Download: Save the chart as PNG
  - Reset: Return to the original view

### Filtering Data

Some visualizations offer filtering options:
- Use dropdown menus to select specific ethical traditions
- Adjust sliders to filter data points by score ranges
- Click on legend items to toggle specific data series

## Text Analysis

### Supported Data Formats

- CSV files
- JSON files
- Excel spreadsheets (.xlsx, .xls)

### Key Metrics

- **Ethics Scores**: Assessment of content through different ethical traditions
- **Bias Score**: Overall measure of potential bias
- **Diversity Index**: Measure of representation diversity
- **Sentiment Analysis**: Positive/negative/neutral sentiment detection
- **Cultural Context Sensitivity**: How content relates to different cultural contexts

## Image Analysis

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)

### Feature Extraction Levels

1. **Basic** (Uses Pillow)
   - Color histograms
   - Basic shape analysis
   - Simple skin tone detection

2. **Medium** (Requires OpenCV)
   - HOG features
   - More accurate skin tone detection
   - Improved shape and texture analysis

3. **Advanced** (Requires TensorFlow)
   - Deep learning features
   - Enhanced demographic detection
   - Cultural element recognition

### Key Metrics

- **Skin Tone Distribution**: Approximation of Fitzpatrick scale representation
- **Gender Distribution**: Estimated gender representation
- **Age Distribution**: Estimated age group representation
- **Cultural Element Detection**: Identification of cultural symbols, clothing, etc.
- **Ethics Scores**: Assessment through different ethical traditions
- **Diversity Index**: Shannon entropy-based measure of representation diversity

## Interpreting Results

### Ethics Scores

Ethics scores range from 0 to 10, where:
- **0-3**: Potentially problematic from this ethical tradition's perspective
- **4-6**: Neutral or mixed assessment
- **7-10**: Aligned with this ethical tradition's principles

### Diversity Index

The diversity index ranges from 0 to 1, where:
- **0**: No diversity (complete homogeneity)
- **0.5**: Moderate diversity
- **1**: Maximum diversity (perfect representation balance)

### Bias Score

Bias scores range from 0 to 10, where:
- **0-3**: Low potential for bias
- **4-6**: Moderate potential for bias
- **7-10**: High potential for bias

### Ethical Traditions Metrics

#### Western Metrics

- **Fairness**: Equal treatment and opportunity across groups
- **Autonomy**: Respecting individual choice and freedom
- **Non-maleficence**: Avoiding harm to individuals
- **Justice**: Distribution of benefits and burdens

#### Ubuntu Metrics

- **Community Harmony**: Impact on group relationships and cohesion
- **Communal Benefit**: Collective positive outcomes for all groups
- **Relational Fairness**: How relationships between groups are affected
- **Shared Dignity**: Recognition of common humanity across groups

#### Confucian Metrics

- **Role Appropriateness**: Alignment with social roles and expectations
- **Social Harmony**: Maintenance of balanced social relationships
- **Reciprocity**: Balance of giving and receiving across groups
- **Ritual Propriety**: Adherence to cultural appropriateness

#### Islamic Metrics

- **Adl (Justice)**: Fairness in distribution and treatment
- **Ihsan (Excellence)**: Going beyond bare minimum in ethical treatment
- **Karama (Dignity)**: Preserving human dignity across all groups
- **Maslaha (Public Interest)**: Benefit to the collective community

## Advanced Configurations

### Performance Optimization

For large datasets:
- Use `--batch-size` to adjust processing chunk size
- Select appropriate `--feature-level` based on computational resources
- Use `--no-dashboard` to skip the interactive visualization
- Consider using a subset of ethical traditions with `--traditions`

### Processing Multiple Files

You can process multiple files by using wildcards in bash:

```bash
# Create a list of image files
find data/marketing_images -name "*.jpg" > image_list.txt

# Process images in batches
python run.py --image-dir data/marketing_images --batch-size 50
```

### Customizing Visualization Appearance

You can customize dashboard appearance by modifying the visualization.py file:

```python
# In visualization.py
# Change color scheme
color_scheme = {
    'western': '#003366',
    'ubuntu': '#006633',
    'confucian': '#660033',
    'islamic': '#333366'
}

# Apply to visualizations
fig.update_traces(marker_color=color_scheme[tradition])
```

## Troubleshooting

### Common Issues

**Issue**: Dashboard shows "No results available"
**Solution**: Ensure your data paths are correct and the files contain valid data

**Issue**: Image analysis is slow
**Solution**: Use a smaller batch size or lower feature extraction level

**Issue**: Missing dependencies error
**Solution**: Run `pip install -r requirements.txt` to install required packages

**Issue**: Memory errors with large datasets
**Solution**: Process data in smaller chunks or reduce feature extraction complexity

### Getting Help

If you encounter problems not covered in this guide:
- Check the project README for additional information
- Look for error messages in the console output
- Review the logs in the output directory

## Visualization Types

The EthiViz dashboard includes several key visualization types:

### Text Analysis Visualizations

- **Ethics Scores Box Plots**: Compare scores across different ethical traditions
- **Bias Distribution Histogram**: Distribution of bias scores across the dataset
- **Diversity vs. Bias Scatter Plot**: Relationship between diversity and bias metrics

### Image Analysis Visualizations

- **Skin Tone Distribution Chart**: Shows representation across skin tone categories
- **Gender Distribution Chart**: Display gender representation in images
- **Diversity Index Bar Chart**: Diversity scores by image
- **Ethics Scores by Tradition**: Compare how images score across ethical traditions
- **Image Gallery**: Display of analyzed images with their key metrics

### Combined Analysis Visualizations

- **Text vs. Image Bias Comparison**: Box plots comparing bias scores
- **Diversity Index Comparison**: Compares diversity between text and image data
- **Ethics Score Comparison**: Comparison of ethical perspectives across data types

## Ethical Traditions

EthiViz analyzes data through multiple ethical traditions:

### Western Ethics

Based on principles like autonomy, beneficence, non-maleficence, and justice. Western ethics prioritizes individual rights, fairness, and equal treatment.

### Ubuntu Ethics

Stems from the African philosophy of "I am because we are." Ubuntu ethics emphasizes communal relationships, shared humanity, and collective well-being over individual interests.

### Confucian Ethics

Focuses on proper relationships, social harmony, and virtues. Confucian ethics emphasizes role fulfillment, hierarchical relationships, and the importance of societal order.

### Islamic Ethics

Centers on justice, dignity, and community welfare. Islamic ethics balances individual rights with societal obligations and emphasizes the inherent dignity of all people.

## Using the Streamlit Interface

EthiViz now includes a modern, intuitive Streamlit interface that makes it easy to analyze data without writing code.

### Starting the Application

To launch the Streamlit interface:

```bash
streamlit run app.py
```

This will open a web browser with the EthiViz application.

### Interface Layout

The interface consists of:

1. **Sidebar**: Contains all input controls and analysis settings
   - Data source selection
   - Ethical tradition selection
   - Advanced options
   - Run button

2. **Main Area**: Displays analysis results in a tabbed interface
   - Text Analysis tab
   - Image Analysis tab
   - Combined Analysis tab

### Workflow

1. **Select Data Sources**:
   - For text data: Upload a CSV/Excel file or use sample data
   - For image data: Upload images or use sample images

2. **Configure Analysis**:
   - Select which ethical traditions to include
   - Adjust advanced options if needed (feature level, batch size, etc.)

3. **Run Analysis**:
   - Click the "Run Analysis" button
   - A progress bar will show analysis status

4. **Explore Results**:
   - Navigate between tabs to view different aspects of the analysis
   - Interact with visualizations (hover, zoom, download)
   - View raw data tables

### Data Upload Guidelines

- **Text Data**: CSV or Excel files with text content
- **Images**: JPG, JPEG, PNG, or GIF files
- **File Size**: Keep individual files under 200MB for best performance

---
