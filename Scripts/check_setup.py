#!/usr/bin/env python3
"""
EthiViz - Cultural Bias Analysis Platform
Setup verification script
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path
import json

def check_dependency(module_name, friendly_name=None):
    """Check if a Python module is available and return its version."""
    friendly_name = friendly_name or module_name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✅ {friendly_name} is installed (version: {version})")
        return True
    except ImportError:
        print(f"❌ {friendly_name} is not installed")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists and print its status."""
    if os.path.exists(file_path):
        print(f"✅ {description} is available at: {file_path}")
        return True
    else:
        print(f"❌ {description} is missing: {file_path}")
        return False

def count_samples(dir_path, pattern="*"):
    """Count the number of files in a directory that match a pattern."""
    if os.path.exists(dir_path):
        count = len(list(Path(dir_path).glob(pattern)))
        return count
    return 0

def read_sample_data(file_path, max_samples=3):
    """Read and display a preview of sample data."""
    extension = os.path.splitext(file_path)[1].lower()
    try:
        if extension == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                sample_count = min(len(data), max_samples)
                print(f"\nPreview of {sample_count} samples from {file_path}:")
                for i, sample in enumerate(data[:sample_count]):
                    if isinstance(sample, dict) and 'text' in sample:
                        preview = sample['text'][:100] + "..." if len(sample['text']) > 100 else sample['text']
                        print(f"  Sample {i+1}: {preview}")
                        if 'category' in sample:
                            print(f"    Category: {sample['category']}")
        elif extension == '.csv':
            # Simple CSV reader without pandas dependency
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            headers = lines[0].strip().split(',')
            print(f"\nPreview of {min(len(lines)-1, max_samples)} samples from {file_path}:")
            print(f"  Headers: {headers}")
            
            for i, line in enumerate(lines[1:max_samples+1]):
                values = line.strip().split(',')
                print(f"  Sample {i+1}: {dict(zip(headers, values))}")
    except Exception as e:
        print(f"Error reading sample data: {e}")

def main():
    """Check the setup of EthiViz."""
    print("\n===== EthiViz Setup Verification =====\n")
    
    # Get application directory
    app_dir = Path(__file__).parent.absolute()
    print(f"Application directory: {app_dir}")
    
    # Check core files
    print("\n----- Core Files -----")
    check_file_exists(app_dir / "app.py", "Streamlit application")
    check_file_exists(app_dir / "run.py", "Runner script")
    check_file_exists(app_dir / "text_analyzer.py", "Text analyzer module")
    check_file_exists(app_dir / "image_analyzer.py", "Image analyzer module")
    check_file_exists(app_dir / "requirements.txt", "Requirements file")
    
    # Check sample data
    print("\n----- Sample Data -----")
    sample_texts_json = app_dir / "sample_texts.json"
    sample_texts_csv = app_dir / "sample_texts.csv"
    sample_images_dir = app_dir / "sample_images"
    
    has_json = check_file_exists(sample_texts_json, "Sample text data (JSON)")
    has_csv = check_file_exists(sample_texts_csv, "Sample text data (CSV)")
    
    if has_json:
        read_sample_data(sample_texts_json)
    elif has_csv:
        read_sample_data(sample_texts_csv)
    
    if os.path.isdir(sample_images_dir):
        img_count = count_samples(sample_images_dir, "*.jpg") + count_samples(sample_images_dir, "*.png")
        print(f"✅ Sample images directory contains {img_count} images")
    else:
        print(f"❌ Sample images directory is missing: {sample_images_dir}")
    
    # Check Python core dependencies
    print("\n----- Core Dependencies -----")
    core_deps = ["numpy", "pandas", "streamlit", "matplotlib", "plotly"]
    for dep in core_deps:
        check_dependency(dep)
    
    # Check optional dependencies
    print("\n----- Optional Dependencies -----")
    optional_deps = [
        ("spacy", "spaCy (for advanced text analysis)"),
        ("nltk", "NLTK (for text processing)"),
        ("cv2", "OpenCV (for medium-level image processing)"),
        ("tensorflow", "TensorFlow (for advanced image analysis)"),
        ("transformers", "Transformers (for advanced text analysis)")
    ]
    for dep, desc in optional_deps:
        check_dependency(dep, desc)
    
    # Summary
    print("\n===== Setup Summary =====")
    print("To launch EthiViz with the Streamlit interface, run:")
    print("  python run.py")
    print("Or directly with Streamlit:")
    print("  streamlit run app.py")
    print("\nTo install missing dependencies:")
    print("  pip install -r requirements.txt")
    
    print("\nFor more information, refer to the README.md file.")

if __name__ == "__main__":
    main()