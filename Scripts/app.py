#!/usr/bin/env python3
"""
EthiViz - Cultural Bias Analysis Platform
Streamlit front-end application for analyzing cultural bias in text and image data
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError
import plotly.express as px
import plotly.graph_objects as go
import base64
import tempfile
import shutil
from dataclasses import asdict
from image_analyzer import ImageAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ethiviz.app')

# Add parent directory to path so we can import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
logger.info(f"Added {parent_dir} to sys.path")

# --- Use Enhanced EthiViz analyzers ---
try:
    from Enhanced_Analysis import HybridTextAnalyzer as TextAnalyzer, HybridImageAnalyzer as ImageAnalyzer
    from Enhanced_Analysis import TextAnalysisResult, ImageAnalysisResult
    HAS_TEXT_ANALYZER = True
    HAS_IMAGE_ANALYZER = True
    logger.info("Enhanced analyzers imported successfully.")
except ImportError as e:
    logger.warning(f"Could not import Enhanced_Analysis module: {e}. Analysis disabled.")
    HAS_TEXT_ANALYZER = False
    HAS_IMAGE_ANALYZER = False
    TextAnalysisResult = None
    ImageAnalysisResult = None

# Set page configuration
st.set_page_config(
    page_title="EthiViz - Cultural Bias Analysis Platform",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "EthiViz - A platform for analyzing cultural bias through multiple ethical traditions"
    }
)

# Apply dark theme CSS and include D3.js (Same as before)
st.markdown("""
<style>
    :root {
        --background-color: #0E1117;
        --secondary-background-color: #262730;
        --primary-color: #4D69FF;
        --secondary-color: #B4ADEA;
        --text-color: #FAFAFA;
        --font: 'Source Sans Pro', sans-serif;
    }
    .main { background-color: var(--background-color); color: var(--text-color); }
    .sidebar .sidebar-content { background-color: var(--secondary-background-color); }
    h1, h2, h3, h4, h5, h6 { color: var(--text-color); font-family: var(--font); }
    .custom-card { background-color: var(--secondary-background-color); border-radius: 10px; padding: 20px; margin-bottom: 20px; border: 1px solid #333; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: flex-start; }
    .metric-card { background-color: rgba(77, 105, 255, 0.1); border-radius: 8px; padding: 15px 20px; flex-basis: 200px; flex-grow: 1; border-left: 5px solid var(--primary-color); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .metric-card h2 { color: var(--primary-color); margin-top: 5px; margin-bottom: 5px; }
    .metric-card h3 { font-size: 1rem; margin-bottom: 5px; }
    .metric-card p { font-size: 0.85rem; color: #AAAAAA; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { height: 45px; white-space: pre-wrap; background-color: transparent; border-radius: 6px 6px 0 0; gap: 1px; padding: 10px 15px; border: none; }
    .stTabs [aria-selected="true"] { background-color: rgba(77, 105, 255, 0.15); border-bottom: 3px solid var(--primary-color); color: var(--primary-color); font-weight: 600; }
    .uploadedFile { background-color: var(--secondary-background-color) !important; border: 1px dashed var(--primary-color) !important; border-radius: 8px !important; }
    .stButton>button { background-color: var(--primary-color); color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; transition: background-color 0.2s ease; }
    .stButton>button:hover { background-color: #3A56E0; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .stButton>button:disabled { background-color: #555; color: #999; cursor: not-allowed; }
    .stProgress>div>div { background-color: var(--primary-color); }
    .d3-container { background-color: var(--secondary-background-color); border-radius: 10px; padding: 20px; margin-bottom: 20px; width: 100%; min-height: 300px; border: 1px solid #333; }
    .d3-container .axis path, .d3-container .axis line { fill: none; stroke: #555; shape-rendering: crispEdges; }
    .d3-container .axis text { fill: #AAAAAA; font-size: 11px; }
    .d3-container .bar:hover { opacity: 1.0 !important; }
</style>
<script src="https://d3js.org/d3.v7.min.js"></script>
""", unsafe_allow_html=True)

# Helper functions
def load_image(image_path):
    """Load an image from path using PIL."""
    try: img = Image.open(image_path); img.load(); return img.convert('RGB')
    except FileNotFoundError: logger.error(f"Image file not found: {image_path}"); return None
    except UnidentifiedImageError: logger.error(f"Unidentified image error: {image_path}"); return None
    except Exception as e: logger.error(f"Error loading image {image_path}: {e}", exc_info=True); return None

def encode_image_to_base64(image_path):
    """Encode an image file to base64."""
    try:
        with open(image_path, 'rb') as f: return base64.b64encode(f.read()).decode('ascii')
    except Exception as e: logger.error(f"Error encoding image {image_path}: {e}"); return None

def create_tradition_radar_chart(data, traditions):
    """Create a radar chart comparing ethical tradition scores."""
    categories = [t.capitalize() for t in traditions]
    values = [pd.to_numeric(data.get(f"{trad}_ethics_score", 0), errors='coerce') for trad in traditions]
    values = [v if pd.notna(v) else 0.0 for v in values]
    fig = go.Figure(); fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Ethics Scores', line_color='#4D69FF', fillcolor='rgba(77, 105, 255, 0.3)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10], showline=False, gridcolor='#444'), angularaxis=dict(gridcolor='#444')), showlegend=False, margin=dict(l=40, r=40, t=50, b=40), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FAFAFA')
    return fig

# --- create_d3_visualization CORRECTED ---
def create_d3_visualization_data(container_id, data, title="D3 Visualization"):
    """Create a D3.js visualization with interactivity."""
    # Data validation
    if not isinstance(data, list):
        if isinstance(data, dict): data = [data]
        else: logger.warning(f"Unsupported D3 data type: {type(data)}."); return f"<div class='d3-container'><h3>{title}</h3><p>Error: Invalid data.</p></div>"
    vis_data = []; traditions = ['western', 'ubuntu', 'confucian', 'islamic']; item_id_counter = 0
    for item in data:
        if not isinstance(item, dict): continue
        entry = {"id": "item" + str(item_id_counter)}; has_data = False
        if "type" in item: entry["type"] = item["type"]
        for tradition in traditions:
            key = f"{tradition}_ethics_score"; score = item.get(key)
            numeric_score = pd.to_numeric(score, errors='coerce')
            entry[tradition] = 0.0 if pd.isna(numeric_score) else float(numeric_score)
            if entry[tradition] > 0: has_data = True
        if has_data: vis_data.append(entry); item_id_counter += 1
    if not vis_data: logger.warning("No valid data for D3 viz."); return f"<div class='d3-container'><h3>{title}</h3><p>No data available.</p></div>"
    try: json_data = json.dumps(vis_data)
    except TypeError as e: logger.error(f"D3 JSON Error: {e}"); return f"<div class='d3-container'><h3>{title}</h3><p>Error: {e}.</p></div>"

    # HTML and JavaScript
    html = f"""
    <div class="d3-container"><div id="{container_id}" style="width: 100%; height: 400px; min-height: 300px;"></div></div>
    <script>
    (function() {{ /* D3 Code with transitions and tooltips */
        const containerId = '{container_id}'; const container = document.getElementById(containerId); if (!container) {{ console.error('D3 container not found:', containerId); return; }}
        const data = {json_data}; if (!data || data.length === 0) {{ container.innerHTML = '<p style="color: #AAAAAA; text-align: center; margin-top: 50px;">No data available.</p>'; return; }}
        // --- CORRECTED CONSOLE LOG ---
        console.log("D3 data for " + containerId + ":", data);
        // --- END CORRECTION ---
        const width = container.clientWidth > 0 ? container.clientWidth : 600; const height = 400; const margin={{top: 50, right: 30, bottom: 50, left: 50}}; const innerWidth = width - margin.left - margin.right; const innerHeight = height - margin.top - margin.bottom;
        const tooltip = d3.select('body').append('div').attr('id', 'tooltip-' + containerId).style('position', 'absolute').style('visibility', 'hidden').style('background-color', 'rgba(40, 40, 40, 0.9)').style('color', '#FAFAFA').style('border', '1px solid #555').style('border-radius', '4px').style('padding', '8px 12px').style('font-size', '12px').style('pointer-events', 'none').style('z-index', '10');
        d3.select('#' + containerId).select('svg').remove();
        const svg = d3.select('#' + containerId).append('svg').attr('viewBox', `0 0 ${{width}} ${{height}}`).attr('preserveAspectRatio', 'xMidYMid meet').style('width', '100%').style('height', 'auto');
        const g = svg.append('g').attr('transform', `translate(${{margin.left}}, ${{margin.top}})`);
        const traditions = ['western', 'ubuntu', 'confucian', 'islamic']; const colors = ['#4D69FF', '#00CC96', '#EF553B', '#AB63FA'];
        const xScale = d3.scaleBand().domain(traditions).range([0, innerWidth]).padding(0.3);
        const yScale = d3.scaleLinear().domain([0, 10]).nice().range([innerHeight, 0]);
        const colorScale = d3.scaleOrdinal().domain(traditions).range(colors);
        g.append('g').attr('class', 'x-axis axis').attr('transform', `translate(0, ${{innerHeight}})`).call(d3.axisBottom(xScale).tickFormat(d => d.charAt(0).toUpperCase() + d.slice(1))).selectAll('text').style('fill', '#AAAAAA').style('font-size', '11px');
        g.append('g').attr('class', 'y-axis axis').call(d3.axisLeft(yScale)).selectAll('text').style('fill', '#AAAAAA');
        g.append('text').attr('transform', 'rotate(-90)').attr('y', 0 - margin.left).attr('x', 0 - (innerHeight / 2)).attr('dy', '1em').style('text-anchor', 'middle').style('fill', '#AAAAAA').style('font-size', '12px').text('Ethics Score');
        const averages = traditions.map(tradition => {{ const values = data.map(d => d[tradition] !== undefined ? d[tradition] : 0); return {{ tradition: tradition, average: d3.mean(values) || 0 }}; }});
        console.log("D3 averages for " + containerId + ":", averages); // Also corrected here
        const bars = g.selectAll('.bar').data(averages.filter(d => d.average >= 0)).enter().append('rect').attr('class', 'bar').attr('x', d => xScale(d.tradition)).attr('width', xScale.bandwidth()).attr('fill', d => colorScale(d.tradition)).attr('y', d => yScale(0)).attr('height', 0).attr('opacity', 0.8)
            .on('mouseover', function(event, d) {{ d3.select(this).transition().duration(100).attr('opacity', 1.0); tooltip.style('visibility', 'visible').html(`<strong>${{d.tradition.charAt(0).toUpperCase() + d.tradition.slice(1)}}</strong><br>Avg Score: ${{d.average.toFixed(2)}}`); }})
            .on('mousemove', function(event, d) {{ tooltip.style('top', (event.pageY - 10) + 'px').style('left', (event.pageX + 10) + 'px'); }})
            .on('mouseout', function(event, d) {{ d3.select(this).transition().duration(100).attr('opacity', 0.8); tooltip.style('visibility', 'hidden'); }});
        bars.transition().duration(750).delay((d, i) => i * 75).ease(d3.easeCubicOut).attr('y', d => yScale(d.average)).attr('height', d => innerHeight - yScale(d.average));
        g.selectAll('.label').data(averages.filter(d => d.average >= 0)).enter().append('text').attr('class', 'label').attr('x', d => xScale(d.tradition) + xScale.bandwidth() / 2).attr('y', d => yScale(0)).attr('text-anchor', 'middle').style('fill', '#FAFAFA').style('font-size', '10px').attr('opacity', 0).text(d => d.average.toFixed(1))
             .transition().duration(600).delay((d, i) => 300 + i * 75).ease(d3.easeCubicOut).attr('y', d => yScale(d.average) - 6).attr('opacity', d => d.average > 0.1 ? 1 : 0);
        svg.append('text').attr('x', width / 2).attr('y', margin.top / 2 + 5).attr('text-anchor', 'middle').style('fill', '#FAFAFA').style('font-size', '16px').style('font-weight', 'bold').text('{title}');
    }})();
    </script>
    """
    return html
# --- END create_d3_visualization CORRECTION ---


def format_metric_card(title, value, description, icon="📊"):
    """Formats a metric card."""
    value_str = f"{float(value):.2f}" if isinstance(value, (int, float, np.number)) and pd.notna(value) else str(value)
    html = f"""<div class="metric-card"><h3>{icon} {title}</h3><h2>{value_str}</h2><p>{description}</p></div>"""
    return html

def run_text_analysis(text_data_input, traditions, advanced_options):
    """Runs text analysis."""
    if not HAS_TEXT_ANALYZER: st.error("TextAnalyzer module not available."); return None
    try:
        analyzer = TextAnalyzer(traditions=traditions, spacy_model=advanced_options.get("nlp_model", "en_core_web_sm"), max_tokens=advanced_options.get("max_tokens", 10000))
        progress_bar = st.progress(0); status_text = st.empty(); status_text.text("Initializing text analysis..."); progress_bar.progress(10)
        status_text.text("Analyzing text data..."); results = analyzer.analyze(text_data_input); progress_bar.progress(90)
        status_text.text("Finalizing results..."); progress_bar.progress(100); time.sleep(0.5); status_text.empty(); progress_bar.empty()
        return results
    except Exception as e: logger.error(f"Error in text analysis: {e}", exc_info=True); st.error(f"Text analysis error: {e}"); return None

def run_image_analysis(image_paths, feature_level, traditions, batch_size, use_pretrained_models=False): # Added use_pretrained_models
    """Runs image analysis."""
    if not HAS_IMAGE_ANALYZER: st.error("ImageAnalyzer module not available."); return None
    if not image_paths: st.warning("No image paths provided."); return None
    try:
        analyzer = ImageAnalyzer(feature_extraction_method=feature_level, use_pretrained_models=use_pretrained_models, cultural_context={"traditions": traditions}, batch_size=batch_size)
        progress_bar = st.progress(0); status_text = st.empty(); status_text.text("Initializing image analysis..."); progress_bar.progress(10)
        status_text.text(f"Analyzing {len(image_paths)} images..."); results = results = analyzer.analyze_images(image_paths); progress_bar.progress(90)
        status_text.text("Finalizing results..."); progress_bar.progress(100); time.sleep(0.5); status_text.empty(); progress_bar.empty()
        return results
    except Exception as e: logger.error(f"Error in image analysis: {e}", exc_info=True); st.error(f"Image analysis error: {e}"); return None

def safe_mean(series):
    """Calculates mean of a series, ignoring non-numeric and returning NaN."""
    numeric_series = pd.to_numeric(series, errors='coerce').dropna()
    return numeric_series.mean() if not numeric_series.empty else np.nan

def display_text_results(results):
    """Displays text analysis results."""
    # (Same as previous corrected version, including radar chart fix)
    if not results: st.warning("No text analysis results available"); return
    results_list_of_dicts = []
    if isinstance(results, list): valid_results = [res for res in results if res and hasattr(res, 'to_dict')]; results_list_of_dicts = [res.to_dict() for res in valid_results] if valid_results else []
    elif hasattr(results, 'to_dict'): results_list_of_dicts = [results.to_dict()]
    else: st.error(f"Unexpected text results format: {type(results)}"); return
    if not results_list_of_dicts: st.warning("No valid text results to display."); return
    df = pd.DataFrame(results_list_of_dicts); logger.info(f"Displaying text results. DF shape: {df.shape}")
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    if 'bias_score' in df.columns: avg_bias = safe_mean(df['bias_score']); bias_desc = "Low" if avg_bias < 3 else ("Moderate" if avg_bias < 7 else "High") if pd.notna(avg_bias) else "Unknown"; st.markdown(format_metric_card("Avg. Bias Score", avg_bias if pd.notna(avg_bias) else "N/A", f"{bias_desc} potential bias", "⚖️"), unsafe_allow_html=True)
    if 'diversity_index' in df.columns: avg_diversity = safe_mean(df['diversity_index']); st.markdown(format_metric_card("Avg. Diversity Index", avg_diversity if pd.notna(avg_diversity) else "N/A", "Representation balance", "🌈"), unsafe_allow_html=True)
    traditions = ['western', 'ubuntu', 'confucian', 'islamic']
    for tradition in traditions:
        col_name = f'{tradition}_ethics_score'
        if col_name in df.columns: avg_score = safe_mean(df[col_name]); st.markdown(format_metric_card(f"{tradition.capitalize()} Score", avg_score if pd.notna(avg_score) else "N/A", "Ethical alignment", "🧠"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Ethical Traditions", "Bias Analysis", "Raw Data"])
    with tab1:
        st.subheader("Ethical Traditions Analysis"); col1, col2 = st.columns([3, 2])
        with col1: # Box Plot
            tradition_fig = go.Figure(); available_traditions = [t for t in traditions if f'{t}_ethics_score' in df.columns]
            for tradition in available_traditions:
                 y_data = pd.to_numeric(df[f'{tradition}_ethics_score'], errors='coerce').dropna()
                 if not y_data.empty: tradition_fig.add_trace(go.Box(y=y_data, name=tradition.capitalize(), boxmean=True, marker_color={'western': '#4D69FF', 'ubuntu': '#00CC96', 'confucian': '#EF553B', 'islamic': '#AB63FA'}.get(tradition, '#CCCCCC')))
            tradition_fig.update_layout(title="Distribution of Ethical Perspective Scores", yaxis_title="Ethics Score", xaxis_title="Ethical Tradition", template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(tradition_fig, use_container_width=True)
        with col2: # Radar chart
            avg_scores_dict = {f"{trad}_ethics_score": safe_mean(df[f"{trad}_ethics_score"]) for trad in available_traditions if f"{trad}_ethics_score" in df.columns}; avg_scores_dict = {k: v for k, v in avg_scores_dict.items() if pd.notna(v)}
            if avg_scores_dict:
                 tradition_names = [key.replace("_ethics_score", "") for key in avg_scores_dict.keys()]; radar_fig = create_tradition_radar_chart(avg_scores_dict, tradition_names); radar_fig.update_layout(title="Average Ethics Scores"); st.plotly_chart(radar_fig, use_container_width=True)
            else: st.info("Could not calculate average scores for radar chart.")
        # D3 chart
        st.markdown("---"); st.markdown("<h3>Interactive Comparison (D3.js)</h3>", unsafe_allow_html=True)
        container_id = "d3_viz_text_" + str(int(time.time() * 1000)); d3_data = df.to_dict(orient="records"); d3_html = create_d3_visualization(container_id, d3_data, title="Text Ethics Scores (D3.js)"); st.components.v1.html(d3_html, height=450, scrolling=False)
    with tab2: # Bias Analysis
        st.subheader("Bias Analysis"); col1, col2 = st.columns(2)
        with col1: # Bias Histogram
            if 'bias_score' in df.columns:
                bias_data = pd.to_numeric(df['bias_score'], errors='coerce').dropna()
                if not bias_data.empty: bias_fig = px.histogram(bias_data, x='bias_score', title="Distribution of Bias Scores", labels={'bias_score': 'Bias Score'}, color_discrete_sequence=['#FF6B6B'], nbins=max(10, min(len(bias_data)//2, 30))); bias_fig.update_layout(xaxis_title="Bias Score", yaxis_title="Count", template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(bias_fig, use_container_width=True)
                else: st.info("No valid bias score data.")
            else: st.info("Bias score data not found.")
        with col2: # Diversity vs Bias Scatter
            if 'diversity_index' in df.columns and 'bias_score' in df.columns:
                scatter_df = df[['diversity_index', 'bias_score']].copy(); scatter_df['diversity_index'] = pd.to_numeric(scatter_df['diversity_index'], errors='coerce'); scatter_df['bias_score'] = pd.to_numeric(scatter_df['bias_score'], errors='coerce'); scatter_df.dropna(inplace=True)
                if not scatter_df.empty: diversity_fig = px.scatter(scatter_df, x='diversity_index', y='bias_score', title="Bias Score vs. Diversity Index", labels={'diversity_index': 'Diversity Index', 'bias_score': 'Bias Score'}, color_discrete_sequence=['#00CC96'], opacity=0.7, trendline="ols", trendline_color_override="#FF6B6B"); diversity_fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(diversity_fig, use_container_width=True)
                else: st.info("No valid diversity/bias data.")
            else: st.info("Diversity/bias data missing.")
    with tab3: # Raw Data
        st.subheader("Raw Analysis Data"); cols_to_display = [col for col in df.columns if not col.endswith(('_features', '_distribution', '_representation', '_elements')) and col not in ['raw_result', 'image_metadata'] and 'confidence' not in col]
        try: st.dataframe(df[cols_to_display], use_container_width=True)
        except KeyError as e: logger.error(f"Error selecting columns: {e}. Available: {df.columns.tolist()}"); st.warning(f"Display error: {e}"); st.dataframe(df, use_container_width=True)


def display_image_results(results, image_paths):
    """Displays image analysis results."""
    # (Same as previous corrected version)
    if not results: st.warning("No image analysis results available"); return
    flat_results = []; original_paths_map = {Path(p).name: p for p in image_paths}
    if isinstance(results, dict):
        for img_key, img_result_obj in results.items():
            filename = Path(img_key).name; original_path = original_paths_map.get(filename, img_key); result_dict = {'image_path': original_path, 'filename': filename}
            if hasattr(img_result_obj, 'to_dict'):
                try: result_dict.update(img_result_obj.to_dict())
                except Exception as e: logger.error(f"Convert fail {filename}: {e}"); result_dict['error'] = f"Convert fail: {e}"
            elif isinstance(img_result_obj, dict): result_dict.update(img_result_obj)
            else: logger.warning(f"Unexpected type {filename}: {type(img_result_obj)}"); result_dict['raw_result'] = str(img_result_obj)
            flat_results.append(result_dict)
    else: st.error(f"Unexpected image results format: {type(results)}"); return
    if not flat_results: st.warning("Could not process image results."); return
    df = pd.DataFrame(flat_results); logger.info(f"Displaying image results. DF shape: {df.shape}")
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    if 'diversity_index' in df.columns: avg_diversity = safe_mean(df['diversity_index']); st.markdown(format_metric_card("Avg. Diversity", avg_diversity if pd.notna(avg_diversity) else "N/A", "Visual representation", "🌈"), unsafe_allow_html=True)
    if 'bias_score' in df.columns: avg_bias = safe_mean(df['bias_score']); bias_desc = "Low" if avg_bias < 3 else ("Moderate" if avg_bias < 7 else "High") if pd.notna(avg_bias) else "Unknown"; st.markdown(format_metric_card("Avg. Bias Score", avg_bias if pd.notna(avg_bias) else "N/A", f"{bias_desc} potential bias", "⚖️"), unsafe_allow_html=True)
    traditions = ['western', 'ubuntu', 'confucian', 'islamic']
    for tradition in traditions:
        col_name = f'{tradition}_ethics_score';
        if col_name in df.columns: avg_score = safe_mean(df[col_name]); st.markdown(format_metric_card(f"{tradition.capitalize()} Score", avg_score if pd.notna(avg_score) else "N/A", "Ethical alignment", "🧠"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Demographics", "Ethical Analysis", "Image Gallery", "Raw Data"])
    with tab1: # Demographics
        st.subheader("Demographic Distribution Analysis"); col1, col2 = st.columns(2)
        def plot_distribution(df, column_name, title, chart_type='bar'):
            if column_name not in df.columns: st.info(f"'{column_name}' data not found."); return False
            data_list = []
            for _, row in df.iterrows():
                dist_data = row[column_name];
                if isinstance(dist_data, dict):
                    for category, value in dist_data.items():
                        if category in ["estimation_confidence", "error"]: continue
                        numeric_value = pd.to_numeric(value, errors='coerce')
                        if pd.notna(numeric_value): data_list.append({'image': row['filename'], 'category': category, 'value': numeric_value})
            if not data_list: st.info(f"No valid data for {title}."); return False
            dist_df = pd.DataFrame(data_list); agg_df = dist_df.groupby('category')['value'].mean().reset_index()
            if chart_type == 'bar': fig = px.bar(agg_df, x='category', y='value', title=title, labels={'value': 'Avg. Presence', 'category': 'Category'}, color_discrete_sequence=px.colors.qualitative.Pastel1)
            elif chart_type == 'pie': fig = px.pie(agg_df, values='value', names='category', title=title, color_discrete_sequence=px.colors.qualitative.Pastel1)
            else: st.error("Invalid chart type"); return False
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True); return True
        with col1: plot_distribution(df, 'skin_tone_distribution', "Average Skin Tone Distribution", 'bar')
        with col2: plot_distribution(df, 'gender_representation', "Average Gender Distribution", 'pie')
        if 'diversity_index' in df.columns:
            diversity_data = df[['filename', 'diversity_index']].copy(); diversity_data['diversity_index'] = pd.to_numeric(diversity_data['diversity_index'], errors='coerce'); diversity_data.dropna(inplace=True)
            if not diversity_data.empty: diversity_fig = px.bar(diversity_data.sort_values('diversity_index', ascending=False), x='filename', y='diversity_index', title="Diversity Index by Image", labels={'diversity_index': 'Diversity Index', 'filename': 'Image'}, color='diversity_index', color_continuous_scale=px.colors.sequential.Viridis); diversity_fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45); st.plotly_chart(diversity_fig, use_container_width=True)
            else: st.info("No valid diversity index data.")
        else: st.info("Diversity index data not found.")
    with tab2: # Ethical Analysis
        st.subheader("Ethical Traditions Analysis"); ethics_scores = []
        for _, row in df.iterrows():
            for tradition in traditions: col_name = f'{tradition}_ethics_score'; score = row.get(col_name); score_numeric = pd.to_numeric(score, errors='coerce');
            if pd.notna(score_numeric): ethics_scores.append({'image': row['filename'], 'tradition': tradition.capitalize(), 'score': score_numeric})
        if ethics_scores:
            ethics_df = pd.DataFrame(ethics_scores)
            ethics_fig = px.bar(ethics_df, x='image', y='score', color='tradition', barmode='group', title="Ethics Scores by Tradition Across Images", labels={'score': 'Ethics Score', 'image': 'Image', 'tradition': 'Tradition'}, color_discrete_map={'Western': '#4D69FF', 'Ubuntu': '#00CC96', 'Confucian': '#EF553B', 'Islamic': '#AB63FA'})
            ethics_fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45); st.plotly_chart(ethics_fig, use_container_width=True)
            st.markdown("---"); st.markdown("#### Detailed View per Image"); col1, col2 = st.columns([1, 2])
            with col1:
                image_options = sorted(df['filename'].unique()); selected_image_filename = None
                if image_options: selected_image_filename = st.selectbox("Select image:", options=image_options, key="img_select_radar")
                else: st.warning("No images found.")
                if selected_image_filename: # Display image below selectbox
                    img_path = df.loc[df['filename'] == selected_image_filename, 'image_path'].iloc[0]; img = load_image(img_path)
                    if img: st.image(img, caption=selected_image_filename, use_column_width=True)
            with col2:
                if 'selected_image_filename' in locals() and selected_image_filename:
                    selected_data = ethics_df[ethics_df['image'] == selected_image_filename]
                    if not selected_data.empty:
                        img_ethics_scores = {f"{row['tradition'].lower()}_ethics_score": row['score'] for _, row in selected_data.iterrows()}
                        available_traditions_img = [t.lower() for t in selected_data['tradition']]
                        if available_traditions_img: radar_fig_img = create_tradition_radar_chart(img_ethics_scores, available_traditions_img); radar_fig_img.update_layout(title=f"Ethical Analysis: {selected_image_filename}", height=400); st.plotly_chart(radar_fig_img, use_container_width=True)
                        else: st.info(f"No valid scores for {selected_image_filename}.")
                    else: st.info(f"No ethics scores for {selected_image_filename}.")
        else: st.info("No valid ethics score data found in image results.")
    with tab3: # Image Gallery
        st.subheader("Image Gallery");
        if df.empty or 'image_path' not in df.columns: st.warning("No images processed/paths unavailable.")
        else:
            num_cols = 4; cols = st.columns(num_cols); image_count = 0
            for idx, row in df.iterrows():
                img_path = row['image_path']; filename = row['filename']; img = load_image(img_path)
                if img:
                    col_index = image_count % num_cols
                    with cols[col_index]:
                        st.markdown(f"<div class='custom-card' style='padding: 10px;'>", unsafe_allow_html=True); st.image(img, caption=f"{filename[:20]}..." if len(filename)>20 else filename, use_column_width=True)
                        metrics_html = ""; bias_score = row.get('bias_score'); diversity_idx = row.get('diversity_index')
                        if pd.notna(pd.to_numeric(bias_score, errors='coerce')): metrics_html += f"Bias: {float(bias_score):.2f}<br>"
                        if pd.notna(pd.to_numeric(diversity_idx, errors='coerce')): metrics_html += f"Div: {float(diversity_idx):.2f}"
                        if metrics_html: st.markdown(f"<p style='font-size: small; text-align: center; margin-top: 5px;'>{metrics_html}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True); image_count += 1
                else: logger.warning(f"Could not load gallery image: {img_path}")
    with tab4: # Raw Data
        st.subheader("Raw Analysis Data")
        cols_to_display = [c for c in df.columns if not c.endswith(('_distribution', '_representation', '_elements')) and c not in ['image_path', 'raw_result', 'image_metadata'] and 'confidence' not in c]
        try: st.dataframe(df[cols_to_display], use_container_width=True)
        except KeyError as e: logger.error(f"Error selecting raw img cols: {e}. Available: {df.columns.tolist()}"); st.warning(f"Display error: {e}"); st.dataframe(df, use_container_width=True)


def display_combined_results(text_results, image_results):
    """Displays combined analysis results."""
    # (Same as previous corrected version)
    if not text_results or not image_results: st.warning("Combined analysis needs both results."); return
    valid_text_results = [];
    if isinstance(text_results, list): valid_text_results = [res.to_dict() for res in text_results if hasattr(res, 'to_dict')]
    elif hasattr(text_results, 'to_dict'): valid_text_results = [text_results.to_dict()]
    text_df = pd.DataFrame(valid_text_results) if valid_text_results else pd.DataFrame()
    flat_image_results = []
    if isinstance(image_results, dict):
        for img_key, img_result_obj in image_results.items():
            result_dict = {'filename': Path(img_key).name}
            if hasattr(img_result_obj, 'to_dict'): result_dict.update(img_result_obj.to_dict())
            elif isinstance(img_result_obj, dict): result_dict.update(img_result_obj)
            flat_image_results.append(result_dict)
    image_df = pd.DataFrame(flat_image_results) if flat_image_results else pd.DataFrame()
    if text_df.empty or image_df.empty: st.warning("Could not prepare data for combined analysis."); return
    st.subheader("Text vs. Image Analysis Comparison"); tab1, tab2 = st.tabs(["Ethics Comparison", "Diversity & Bias"])
    with tab1:
        st.markdown("#### Average Ethical Scores"); traditions = ['western', 'ubuntu', 'confucian', 'islamic']; combined_ethics_data = []
        for tradition in traditions: col_name = f'{tradition}_ethics_score'; text_mean = safe_mean(text_df[col_name]) if col_name in text_df else np.nan; image_mean = safe_mean(image_df[col_name]) if col_name in image_df else np.nan
        if pd.notna(text_mean): combined_ethics_data.append({'Source': 'Text', 'Tradition': tradition.capitalize(), 'Average Score': text_mean})
        if pd.notna(image_mean): combined_ethics_data.append({'Source': 'Image', 'Tradition': tradition.capitalize(), 'Average Score': image_mean})
        if combined_ethics_data:
            combined_ethics_df = pd.DataFrame(combined_ethics_data); fig = px.bar(combined_ethics_df, x='Tradition', y='Average Score', color='Source', barmode='group', title="Average Ethics Score: Text vs. Image", labels={'Average Score': 'Avg. Ethics Score'}, color_discrete_map={'Text': '#4D69FF', 'Image': '#00CC96'})
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)
        else: st.info("No comparable ethics score data.")
    with tab2:
        st.markdown("#### Average Diversity Index & Bias Score"); combined_metrics_data = [];
        text_div = safe_mean(text_df['diversity_index']) if 'diversity_index' in text_df else np.nan; image_div = safe_mean(image_df['diversity_index']) if 'diversity_index' in image_df else np.nan
        if pd.notna(text_div): combined_metrics_data.append({'Metric': 'Diversity Index', 'Source': 'Text', 'Value': text_div})
        if pd.notna(image_div): combined_metrics_data.append({'Metric': 'Diversity Index', 'Source': 'Image', 'Value': image_div})
        text_bias = safe_mean(text_df['bias_score']) if 'bias_score' in text_df else np.nan; image_bias = safe_mean(image_df['bias_score']) if 'bias_score' in image_df else np.nan
        if pd.notna(text_bias): combined_metrics_data.append({'Metric': 'Bias Score', 'Source': 'Text', 'Value': text_bias})
        if pd.notna(image_bias): combined_metrics_data.append({'Metric': 'Bias Score', 'Source': 'Image', 'Value': image_bias})
        if combined_metrics_data:
             combined_metrics_df = pd.DataFrame(combined_metrics_data); fig = px.bar(combined_metrics_df, x='Metric', y='Value', color='Source', barmode='group', title="Average Diversity & Bias: Text vs. Image", labels={'Value': 'Average Score'}, color_discrete_map={'Text': '#4D69FF', 'Image': '#00CC96'})
             fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)
        else: st.info("No comparable diversity or bias data.")


# Corrected save_results function
def save_results(text_results, image_results, output_dir):
    """Save analysis results to files after converting to serializable format."""
    try:
        output_path = Path(output_dir); output_path.mkdir(parents=True, exist_ok=True); logger.info(f"Saving results to {output_path}"); success_flags = {'text': False, 'image': False}
        if text_results:
            logger.info("Processing text results for saving..."); serializable_text = None
            try:
                if isinstance(text_results, list): serializable_text = [res.to_dict() for res in text_results if res and hasattr(res, 'to_dict')]
                elif hasattr(text_results, 'to_dict'): serializable_text = text_results.to_dict()
                elif isinstance(text_results, dict): serializable_text = text_results
                else: logger.warning(f"Unexpected text results type ({type(text_results)}). Saving as str."); serializable_text = str(text_results)
                if serializable_text is not None:
                    save_path = output_path / 'text_analysis_results.json';
                    with open(save_path, 'w', encoding='utf-8') as f: json.dump(serializable_text, f, indent=2, ensure_ascii=False, default=str)
                    logger.info(f"Text results saved: {save_path}"); success_flags['text'] = True
                else: logger.warning("No serializable text data to save.")
            except Exception as e: logger.error(f"Error saving text results: {e}", exc_info=True); st.error(f"Failed text save: {e}")
        if image_results:
            logger.info("Processing image results for saving..."); serializable_image_dict = {}
            try:
                if isinstance(image_results, dict):
                    for image_path, result_obj in image_results.items():
                        if hasattr(result_obj, 'to_dict'): serializable_image_dict[str(image_path)] = result_obj.to_dict()
                        elif isinstance(result_obj, dict): serializable_image_dict[str(image_path)] = result_obj
                        else: logger.warning(f"Unexpected image result type ({type(result_obj)}) for {image_path}. Storing str."); serializable_image_dict[str(image_path)] = str(result_obj)
                else: logger.warning(f"Image results not dict ({type(image_results)}). Skipping save.")
                if serializable_image_dict:
                    save_path = output_path / 'image_analysis_results.json';
                    with open(save_path, 'w', encoding='utf-8') as f: json.dump(serializable_image_dict, f, indent=2, ensure_ascii=False, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) # Handle numpy types
                    logger.info(f"Image results saved: {save_path}"); success_flags['image'] = True
                elif isinstance(image_results, dict) and not image_results: logger.info("Image results dict empty.")
                elif isinstance(image_results, dict): logger.warning("No serializable image data generated.")
            except Exception as e: logger.error(f"Error saving image results: {e}", exc_info=True); st.error(f"Failed image save: {e}")
        if success_flags['text'] or success_flags['image']: saved_types = [k for k, v in success_flags.items() if v]; st.success(f"{', '.join(saved_types).capitalize()} results saved to {output_path}")
        elif text_results is None and image_results is None: st.info("No results generated to save.")
        else: st.warning("Result saving completed, but no files saved (check logs/errors).")
        return True
    except Exception as e: logger.error(f"General error in save_results: {e}", exc_info=True); st.error(f"Error setting up results saving: {e}"); return False


def main():
    """Main function for the Streamlit app."""
    # Sidebar setup
    with st.sidebar:
        st.title("EthiViz"); st.markdown("### Cultural Bias Analysis"); st.markdown("---")
        st.markdown("## 1. Input Data"); analysis_type = st.radio("Select Analysis Type", ["Text", "Image", "Text & Image"], index=2, key="analysis_type")
        uploaded_text_data = None; text_data_provided = False
        if "Text" in analysis_type: text_data_option = st.radio("Text Source", ["Upload File (CSV/XLSX)", "Use Sample Data"], index=1, key="text_source"); uploaded_text_data = st.file_uploader("Upload text dataset", type=["csv", "xlsx", "xls"], key="text_upload") if text_data_option == "Upload File (CSV/XLSX)" else None; text_data_provided = bool(uploaded_text_data) or (text_data_option == "Use Sample Data")
        uploaded_images = None; image_data_provided = False
        if "Image" in analysis_type: image_data_option = st.radio("Image Source", ["Upload Images", "Use Sample Images"], index=1, key="image_source"); uploaded_images = st.file_uploader("Upload images", type=["jpg", "jpeg", "png", "gif", "webp"], accept_multiple_files=True, key="image_upload") if image_data_option == "Upload Images" else None; image_data_provided = bool(uploaded_images) or (image_data_option == "Use Sample Images")
        st.markdown("---")
        st.markdown("## 2. Analysis Settings"); available_traditions = ['western', 'ubuntu', 'confucian', 'islamic']; selected_traditions = st.multiselect("Ethical Traditions", options=available_traditions, default=available_traditions)
        with st.expander("Advanced Options"):
            st.markdown("**Text Analysis**"); text_advanced_options = {"max_tokens": st.number_input("Max Tokens per Text", min_value=500, value=10000, step=500, key="text_max_tokens"), "nlp_model": st.selectbox("SpaCy Model (if used)", ["en_core_web_sm", "en_core_web_md"], index=0, key="text_nlp_model")}
            st.markdown("**Image Analysis**"); image_feature_level = st.select_slider("Feature Detail Level", options=["basic", "medium", "advanced"], value="medium", key="img_feat_level", help="Basic: color, Medium: HOG (if cv2), Advanced: TF (if tf)"); image_batch_size = st.slider("Image Batch Size", min_value=1, max_value=64, value=16, key="img_batch")
            st.markdown("**Output**"); output_dir = st.text_input("Save Results Directory", value="./ethiviz_results", key="output_dir")
        st.markdown("---")
        st.markdown("## 3. Run Analysis"); run_button_disabled = not ((text_data_provided and "Text" in analysis_type) or (image_data_provided and "Image" in analysis_type)) or not selected_traditions
        run_button = st.button("🚀 Run Analysis", type="primary", disabled=run_button_disabled, use_container_width=True)
        if run_button_disabled: st.caption("Select data source(s) and tradition(s).")

    # Main content area
    st.title("EthiViz - Cultural Bias Analysis")
    st.markdown("Analyze text and images for cultural bias indicators through multiple ethical lenses.")
    st.markdown("---")

    # Session state init
    if 'text_results' not in st.session_state: st.session_state.text_results = None
    if 'image_results' not in st.session_state: st.session_state.image_results = None
    if 'image_paths' not in st.session_state: st.session_state.image_paths = []
    if 'temp_image_dir' not in st.session_state: st.session_state.temp_image_dir = None

    # Data Loading Logic
    text_data = None
    if "Text" in analysis_type and text_data_provided:
        if text_data_option == "Upload File (CSV/XLSX)" and uploaded_text_data:
            try:
                logger.info(f"Loading: {uploaded_text_data.name}")
                if uploaded_text_data.name.lower().endswith(('.xlsx', '.xls')): text_data = pd.read_excel(uploaded_text_data)
                else: text_data = pd.read_csv(uploaded_text_data)
                text_col = next((col for col in text_data.columns if col.lower() == 'text'), None)
                if not text_col: st.warning("Need 'text' column."); text_data = None
                else:
                    if text_col != 'text': text_data.rename(columns={text_col: 'text'}, inplace=True)
                    st.success(f"Loaded text ({text_data.shape[0]} rows)")
            except Exception as e: logger.error(f"Text load error: {e}", exc_info=True); st.error(f"Text load error: {e}"); text_data = None
        elif text_data_option == "Use Sample Data":
            try:
                logger.info("Loading sample text."); text_data = pd.DataFrame({'text': ["Western democracies prioritize individual rights.", "Ubuntu teaches 'I am because we are'.", "Confucian ethics values social harmony.", "Islamic principles call for justice.", "Autonomy is culturally specific.", "Growth models can neglect community.", "Tradition may hinder progress.", "Misinterpretations create stereotypes."], 'category': ["western", "ubuntu", "confucian", "islamic", "critique-w", "critique-dev", "critique-c", "critique-i"]})
                st.success(f"Using sample text ({text_data.shape[0]} entries).")
            except Exception as e: logger.error(f"Sample text error: {e}", exc_info=True); st.error("Sample text load error."); text_data = None
    if "Image" in analysis_type and image_data_provided:
        if image_data_option == "Upload Images" and uploaded_images:
            process_upload = False;
            if st.session_state.temp_image_dir is None or run_button: process_upload = True
            if process_upload:
                if st.session_state.temp_image_dir and os.path.exists(st.session_state.temp_image_dir):
                    try: shutil.rmtree(st.session_state.temp_image_dir)
                    except Exception as clean_e: logger.warning(f"Could not clean temp dir {st.session_state.temp_image_dir}: {clean_e}")
                temp_dir = tempfile.mkdtemp(prefix="ethiviz_img_"); st.session_state.temp_image_dir = temp_dir; st.session_state.image_paths = []
                logger.info(f"Created temp dir: {temp_dir}")
                with st.spinner(f"Processing {len(uploaded_images)} images..."):
                    # --- CORRECTED IMAGE UPLOAD LOOP ---
                    for img_file in uploaded_images:
                        try:
                            # Define path
                            img_path = os.path.join(temp_dir, img_file.name)
                            # Write file using 'with open'
                            with open(img_path, 'wb') as f:
                                f.write(img_file.getbuffer())
                            # Append path only after successful write
                            st.session_state.image_paths.append(img_path)
                        except Exception as e:
                            logger.error(f"Image save error {img_file.name}: {e}", exc_info=True)
                            st.error(f"Error processing '{img_file.name}': {e}")
                    # --- END CORRECTION ---
                if st.session_state.image_paths: st.success(f"Processed {len(st.session_state.image_paths)} uploaded images.")

        elif image_data_option == "Use Sample Images":
             sample_img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_images")
             logger.info(f"Looking for sample images: {sample_img_dir}")
             if os.path.isdir(sample_img_dir):
                 st.session_state.image_paths = [os.path.join(sample_img_dir, f) for f in os.listdir(sample_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
                 if st.session_state.image_paths: st.success(f"Using {len(st.session_state.image_paths)} sample images.")
                 else: st.warning(f"No images found: {sample_img_dir}"); st.session_state.image_paths = []
             else: st.warning(f"Sample dir not found: {sample_img_dir}"); st.session_state.image_paths = []

    # Run Analysis Logic
    if run_button:
        logger.info("Run Analysis triggered."); st.session_state.text_results = None; st.session_state.image_results = None # Reset results
        run_text = "Text" in analysis_type and text_data is not None; run_image = "Image" in analysis_type and st.session_state.image_paths
        if not run_text and not run_image: st.error("No valid data available for analysis.")
        elif not selected_traditions: st.error("Select at least one ethical tradition.")
        else:
            with st.spinner("Performing analysis... This may take a while."):
                 start_time = time.time()
                 if run_text:
                      logger.info("Starting text analysis..."); text_input = text_data['text'].tolist() if isinstance(text_data, pd.DataFrame) and 'text' in text_data else (text_data if isinstance(text_data, list) else None)
                      if text_input: st.session_state.text_results = run_text_analysis(text_input, selected_traditions, text_advanced_options)
                      else: logger.warning("No valid text input provided."); st.warning("Text input invalid.")
                      logger.info("Text analysis finished.")
                 if run_image:
                      logger.info("Starting image analysis...")
                      img_feat_method = {'basic':'color_histogram', 'medium':'hog', 'advanced':'deep_features'}[image_feature_level]
                      img_use_tf = img_feat_method == 'deep_features'
                      st.session_state.image_results = run_image_analysis(st.session_state.image_paths, img_feat_method, selected_traditions, image_batch_size, use_pretrained_models=img_use_tf)
                      logger.info("Image analysis finished.")
                 end_time = time.time(); st.info(f"Analysis completed in {end_time - start_time:.2f} seconds.")
                 if st.session_state.text_results or st.session_state.image_results: logger.info("Saving results..."); save_results(st.session_state.text_results, st.session_state.image_results, output_dir)
                 else: logger.info("No results generated to save.")

    # Display Results
    show_text_tab = st.session_state.text_results is not None; show_image_tab = st.session_state.image_results is not None; show_combined_tab = show_text_tab and show_image_tab
    tabs_to_create = []
    if show_text_tab: tabs_to_create.append("📊 Text Analysis")
    if show_image_tab: tabs_to_create.append("🖼️ Image Analysis")
    if show_combined_tab: tabs_to_create.append("🔄 Combined Analysis")
    if not tabs_to_create and not run_button: st.info("Configure analysis options and click 'Run Analysis'.")
    elif not tabs_to_create and run_button: st.warning("Analysis ran, but no results were generated (check logs/input data).")
    elif tabs_to_create:
        results_tabs = st.tabs(tabs_to_create); tab_index = 0
        if show_text_tab:
             with results_tabs[tab_index]: logger.info("Displaying Text Analysis tab."); display_text_results(st.session_state.text_results); tab_index += 1
        if show_image_tab:
             with results_tabs[tab_index]: logger.info("Displaying Image Analysis tab."); display_image_results(st.session_state.image_results, st.session_state.image_paths); tab_index += 1
        if show_combined_tab:
             with results_tabs[tab_index]: logger.info("Displaying Combined Analysis tab."); display_combined_results(st.session_state.text_results, st.session_state.image_results); tab_index += 1

    # Footer
    st.markdown("---"); st.caption("EthiViz v0.2.4 - Cultural Bias Analysis Platform") # Incremented version

if __name__ == "__main__":
    logger.info("Starting EthiViz Streamlit App...")
    main()
    logger.info("EthiViz Streamlit App finished.")