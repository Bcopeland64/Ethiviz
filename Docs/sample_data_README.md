# Sample Data for EthiViz

This directory contains sample data files to help you test the EthiViz platform.

## Text Samples

### sample_texts.csv and sample_texts.json

These files contain identical sample texts representing different ethical traditions and approaches. Each sample includes:

1. **text**: The text content to be analyzed
2. **category**: The primary ethical tradition or category represented by the text

The sample texts cover:
- Western ethical traditions
- Ubuntu ethical traditions
- Confucian ethical traditions
- Islamic ethical traditions 
- Mixed and comparative ethical perspectives
- Applied ethics in various domains (business, environment, technology, healthcare, education)

Feel free to add your own samples by extending these files or creating new ones.

## Image Samples

### /sample_images directory

This directory contains sample images that can be used to test the image analysis capabilities of EthiViz. The images come from diverse sources to demonstrate the platform's ability to analyze different types of visual content.

Image analysis will examine:
- Color distributions
- Skin tone representation
- Gender representation
- Age representation
- Cultural elements

## Using the Sample Data

1. Launch EthiViz with `python run.py` or `streamlit run app.py`
2. In the sidebar, select "Sample Data" for text analysis
3. Select "Sample Images" for image analysis
4. Click "Run Analysis" to process the sample data
5. View the results in the different tabs

## Adding Your Own Sample Data

You can add additional sample data:

- For text: Create/update CSV or JSON files following the same structure
- For images: Add image files to the sample_images directory

## Data Usage Rights

The sample data provided is for demonstration purposes only and should not be used for commercial purposes without appropriate permissions.