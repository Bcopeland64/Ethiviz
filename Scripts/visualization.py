#!/usr/bin/env python3
"""
EthiViz - Visualization Module
Creates an interactive dashboard to display text and image analysis results
"""

import json
import logging
from pathlib import Path
import base64
import io

# Dashboard libraries
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger('ethiviz.visualization')

def load_image_base64(image_path):
    """Load image and convert to base64 for display in dashboard."""
    try:
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('ascii')
            return f'data:image/png;base64,{encoded}'
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {e}")
        return None

def create_text_visualizations(text_results):
    """Create visualizations for text analysis results."""
    if not text_results:
        return [html.Div("No text analysis results available")]
    
    visualizations = []
    
    # Convert results to pandas DataFrame for easier visualization
    df = pd.DataFrame(text_results)
    
    # Ethical Traditions Comparison
    tradition_fig = go.Figure()
    traditions = ['western', 'ubuntu', 'confucian', 'islamic']
    for tradition in traditions:
        if f'{tradition}_ethics_score' in df.columns:
            tradition_fig.add_trace(go.Box(
                y=df[f'{tradition}_ethics_score'],
                name=tradition.capitalize(),
                boxmean=True
            ))
    
    tradition_fig.update_layout(
        title="Ethical Perspective Scores Across Dataset",
        yaxis_title="Ethics Score",
        xaxis_title="Ethical Tradition"
    )
    
    visualizations.append(dcc.Graph(figure=tradition_fig))
    
    # Bias Distribution
    if 'bias_score' in df.columns:
        bias_fig = px.histogram(
            df, x='bias_score',
            title="Distribution of Bias Scores",
            labels={'bias_score': 'Bias Score'},
            color_discrete_sequence=['#3366CC']
        )
        bias_fig.update_layout(
            xaxis_title="Bias Score",
            yaxis_title="Count"
        )
        visualizations.append(dcc.Graph(figure=bias_fig))
    
    # Cultural Diversity
    if 'diversity_index' in df.columns:
        diversity_fig = px.scatter(
            df, x='diversity_index', y='bias_score',
            title="Relationship Between Diversity and Bias",
            labels={
                'diversity_index': 'Diversity Index',
                'bias_score': 'Bias Score'
            }
        )
        visualizations.append(dcc.Graph(figure=diversity_fig))
    
    return visualizations

def create_image_visualizations(image_results):
    """Create visualizations for image analysis results."""
    if not image_results:
        return [html.Div("No image analysis results available")]
    
    visualizations = []
    
    # Convert to DataFrame
    flat_results = []
    for img_path, results in image_results.items():
        result = {
            'image_path': img_path,
            'filename': Path(img_path).name
        }
        result.update(results)
        flat_results.append(result)
    
    df = pd.DataFrame(flat_results)
    
    # Skin Tone Distribution
    if 'skin_tone_distribution' in df.columns:
        # Aggregate skin tone data
        skin_tones = ['Type I', 'Type II', 'Type III', 'Type IV', 'Type V', 'Type VI']
        skin_tone_data = []
        
        for _, row in df.iterrows():
            if isinstance(row['skin_tone_distribution'], dict):
                for tone, value in row['skin_tone_distribution'].items():
                    skin_tone_data.append({
                        'image': row['filename'],
                        'skin_tone': tone,
                        'value': value
                    })
        
        if skin_tone_data:
            skin_df = pd.DataFrame(skin_tone_data)
            skin_fig = px.bar(
                skin_df, x='skin_tone', y='value', color='image', barmode='group',
                title="Skin Tone Distribution Across Images"
            )
            visualizations.append(dcc.Graph(figure=skin_fig))
    
    # Gender Distribution
    if 'gender_distribution' in df.columns:
        # Aggregate gender data
        gender_data = []
        
        for _, row in df.iterrows():
            if isinstance(row['gender_distribution'], dict):
                for gender, value in row['gender_distribution'].items():
                    gender_data.append({
                        'image': row['filename'],
                        'gender': gender,
                        'value': value
                    })
        
        if gender_data:
            gender_df = pd.DataFrame(gender_data)
            gender_fig = px.bar(
                gender_df, x='gender', y='value', color='image', barmode='group',
                title="Gender Distribution Across Images"
            )
            visualizations.append(dcc.Graph(figure=gender_fig))
    
    # Diversity Index
    if 'diversity_index' in df.columns:
        diversity_fig = px.bar(
            df, x='filename', y='diversity_index',
            title="Diversity Index by Image",
            labels={'diversity_index': 'Diversity Index', 'filename': 'Image'}
        )
        visualizations.append(dcc.Graph(figure=diversity_fig))
    
    # Ethics Scores by Tradition
    traditions = ['western', 'ubuntu', 'confucian', 'islamic']
    ethics_scores = []
    
    for _, row in df.iterrows():
        for tradition in traditions:
            col_name = f'{tradition}_ethics_score'
            if col_name in row and row[col_name] is not None:
                ethics_scores.append({
                    'image': row['filename'],
                    'tradition': tradition.capitalize(),
                    'score': row[col_name]
                })
    
    if ethics_scores:
        ethics_df = pd.DataFrame(ethics_scores)
        ethics_fig = px.bar(
            ethics_df, x='image', y='score', color='tradition', barmode='group',
            title="Ethics Scores by Tradition Across Images"
        )
        visualizations.append(dcc.Graph(figure=ethics_fig))
    
    # Image Gallery with Results
    image_cards = []
    for idx, row in df.iterrows():
        img_path = row['image_path']
        img_data = load_image_base64(img_path)
        
        if img_data:
            # Extract key metrics
            metrics = {}
            for key in ['diversity_index', 'bias_score']:
                if key in row and row[key] is not None:
                    metrics[key] = row[key]
            
            # Create card
            card = html.Div([
                html.H4(row['filename']),
                html.Img(src=img_data, style={'max-width': '100%', 'max-height': '200px'}),
                html.Div([
                    html.P(f"{k.replace('_', ' ').title()}: {v:.2f}")
                    for k, v in metrics.items()
                ])
            ], style={
                'border': '1px solid #ddd',
                'border-radius': '5px',
                'padding': '10px',
                'margin': '10px',
                'width': '300px',
                'display': 'inline-block'
            })
            
            image_cards.append(card)
    
    if image_cards:
        visualizations.append(html.Div([
            html.H3("Image Gallery"),
            html.Div(image_cards, style={'display': 'flex', 'flex-wrap': 'wrap'})
        ]))
    
    return visualizations

def create_dashboard(text_results=None, image_results=None, port=8050):
    """Create and run an interactive dashboard for EthiViz results."""
    app = dash.Dash(__name__, title="EthiViz - Cultural Bias Analysis Dashboard")
    
    # Layout
    app.layout = html.Div([
        html.H1("EthiViz - Cultural Bias Analysis Dashboard"),
        
        # Tabs for different analysis types
        dcc.Tabs([
            dcc.Tab(label="Text Analysis", children=[
                html.Div(id="text-visualizations", children=create_text_visualizations(text_results))
            ]),
            dcc.Tab(label="Image Analysis", children=[
                html.Div(id="image-visualizations", children=create_image_visualizations(image_results))
            ]),
            dcc.Tab(label="Combined Analysis", children=[
                html.Div(id="combined-visualizations")
            ])
        ]),
        
        # Footer
        html.Footer([
            html.Hr(),
            html.P("EthiViz - Cultural Bias Analysis Platform")
        ])
    ], style={'margin': '20px'})
    
    # Define callbacks for interactive elements
    @app.callback(
        Output('combined-visualizations', 'children'),
        [Input('text-visualizations', 'children'),
         Input('image-visualizations', 'children')]
    )
    def update_combined_view(text_vis, image_vis):
        """Update the combined analysis view."""
        # Only create combined visualizations if both text and image results exist
        if not text_results or not image_results:
            return [html.Div("Combined analysis requires both text and image data")]
        
        # Create combined visualizations here
        combined_vis = []
        
        # Example: Compare bias scores across text and image data
        try:
            text_df = pd.DataFrame(text_results)
            image_df = pd.DataFrame([{
                'image_path': img_path, 
                'filename': Path(img_path).name,
                **results
            } for img_path, results in image_results.items()])
            
            # Compare bias scores
            if 'bias_score' in text_df.columns and 'bias_score' in image_df.columns:
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=text_df['bias_score'],
                    name='Text Data',
                    boxmean=True
                ))
                fig.add_trace(go.Box(
                    y=image_df['bias_score'],
                    name='Image Data',
                    boxmean=True
                ))
                fig.update_layout(
                    title="Bias Score Comparison: Text vs Images",
                    yaxis_title="Bias Score"
                )
                combined_vis.append(dcc.Graph(figure=fig))
            
            # Compare diversity indices
            if 'diversity_index' in text_df.columns and 'diversity_index' in image_df.columns:
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=text_df['diversity_index'],
                    name='Text Data',
                    boxmean=True
                ))
                fig.add_trace(go.Box(
                    y=image_df['diversity_index'],
                    name='Image Data',
                    boxmean=True
                ))
                fig.update_layout(
                    title="Diversity Index Comparison: Text vs Images",
                    yaxis_title="Diversity Index"
                )
                combined_vis.append(dcc.Graph(figure=fig))
            
            # Compare ethical perspectives
            traditions = ['western', 'ubuntu', 'confucian', 'islamic']
            for tradition in traditions:
                col_name = f'{tradition}_ethics_score'
                if col_name in text_df.columns and col_name in image_df.columns:
                    fig = go.Figure()
                    fig.add_trace(go.Box(
                        y=text_df[col_name],
                        name='Text Data',
                        boxmean=True
                    ))
                    fig.add_trace(go.Box(
                        y=image_df[col_name],
                        name='Image Data',
                        boxmean=True
                    ))
                    fig.update_layout(
                        title=f"{tradition.capitalize()} Ethics Score: Text vs Images",
                        yaxis_title="Ethics Score"
                    )
                    combined_vis.append(dcc.Graph(figure=fig))
        
        except Exception as e:
            logger.error(f"Error creating combined visualizations: {e}")
            combined_vis = [html.Div(f"Error creating combined visualizations: {e}")]
        
        return combined_vis
    
    # Run the server
    app.run_server(debug=True, port=port)

if __name__ == '__main__':
    # Example usage when run directly
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python visualization.py <text_results_path> <image_results_path>")
        sys.exit(1)
    
    text_results_path = sys.argv[1]
    image_results_path = sys.argv[2]
    
    # Load results
    with open(text_results_path, 'r') as f:
        text_results = json.load(f)
    
    with open(image_results_path, 'r') as f:
        image_results = json.load(f)
    
    # Create dashboard
    create_dashboard(text_results, image_results)