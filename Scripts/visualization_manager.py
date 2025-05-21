import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import base64
from io import BytesIO
import dataclasses
from dataclasses import dataclass


class VisualizationGenerator:
    """
    Generates interactive visualizations for ethical analysis results
    using JavaScript libraries for web display.
    """
    
    def __init__(self, results: Dict[str, Any], output_dir: str = "visualizations"):
        """
        Initialize with analysis results and output directory
        """
        self.results = results
        self.output_dir = output_dir
        self.visualization_files = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all_visualizations(self) -> Dict[str, str]:
        """
        Generate all visualizations and return paths to the files
        """
        visualizations = {}
        
        # Generate comparative heatmap
        visualizations["tradition_comparison"] = self.generate_tradition_comparison_heatmap()
        
        # Generate intersectional analysis visualization
        if "intersectional_analysis" in self.results:
            visualizations["intersectional"] = self.generate_intersectional_visualization()
        
        # Generate metric comparison across sensitive attributes
        visualizations["metric_comparison"] = self.generate_metric_comparison_chart()
        
        # Generate recommendation dashboard
        if "recommendations" in self.results:
            visualizations["recommendations"] = self.generate_recommendation_dashboard()
        
        # Generate cultural inclusion index visualization
        if "integrated_analysis" in self.results and "cultural_inclusion_index" in self.results["integrated_analysis"]:
            visualizations["cultural_inclusion"] = self.generate_cultural_inclusion_visualization()
        
        # Generate custom chord diagram for inter-group relationships
        visualizations["group_relationships"] = self.generate_group_relationship_diagram()
        
        return visualizations
    
    def generate_tradition_comparison_heatmap(self) -> str:
        """
        Generate a heatmap comparing metrics across different ethical traditions
        """
        filename = f"{self.output_dir}/tradition_comparison_heatmap.html"
        
        # Extract metrics for each tradition
        tradition_metrics = {}
        if "tradition_analysis" in self.results:
            for tradition, metrics in self.results["tradition_analysis"].items():
                tradition_metrics[tradition] = {}
                for metric_name, results in metrics.items():
                    # Extract numeric values for visualization
                    for key, value in results.items():
                        if isinstance(value, (int, float)) and "disparity" in key or "harmony" in key:
                            tradition_metrics[tradition][f"{metric_name}_{key}"] = value
        
        # Generate HTML with interactive heatmap using D3.js
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Ethical Tradition Comparison</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                #heatmap { margin: 20px 0; }
                .cell { stroke: #eee; }
                .cell:hover { stroke: #555; stroke-width: 1px; }
                .legend { margin-top: 20px; }
                .axis-label { font-size: 12px; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="title">Comparison of Ethical Metrics Across Traditions</div>
            <div id="heatmap"></div>
            <div class="legend" id="legend"></div>
            
            <script>
            // Data from Python analysis
            const data = """ + json.dumps(tradition_metrics) + """;
            
            // Process data for heatmap format
            const traditions = Object.keys(data);
            const allMetrics = new Set();
            const heatmapData = [];
            
            // Collect all unique metrics
            traditions.forEach(tradition => {
                Object.keys(data[tradition]).forEach(metric => {
                    allMetrics.add(metric);
                });
            });
            
            const metrics = Array.from(allMetrics);
            
            // Create heatmap data structure
            traditions.forEach(tradition => {
                metrics.forEach(metric => {
                    heatmapData.push({
                        tradition: tradition,
                        metric: metric,
                        value: data[tradition][metric] || 0
                    });
                });
            });
            
            // Set up dimensions
            const margin = {top: 50, right: 50, bottom: 150, left: 150};
            const width = Math.max(600, metrics.length * 60);
            const height = traditions.length * 60;
            
            // Create color scale - blue for low values (good), red for high values (concerning)
            const colorScale = d3.scaleSequential()
                .domain([0, d3.max(heatmapData, d => d.value)])
                .interpolator(d3.interpolateRdYlBu);
            
            // Create SVG
            const svg = d3.select("#heatmap")
                .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Create x scale (metrics)
            const x = d3.scaleBand()
                .range([0, width])
                .domain(metrics)
                .padding(0.05);
            
            // Create y scale (traditions)
            const y = d3.scaleBand()
                .range([0, height])
                .domain(traditions)
                .padding(0.05);
            
            // Add x axis
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .attr("transform", "rotate(-45)")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em");
            
            // Add y axis
            svg.append("g")
                .call(d3.axisLeft(y));
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Add cells
            svg.selectAll()
                .data(heatmapData)
                .enter()
                .append("rect")
                .attr("class", "cell")
                .attr("x", d => x(d.metric))
                .attr("y", d => y(d.tradition))
                .attr("width", x.bandwidth())
                .attr("height", y.bandwidth())
                .attr("fill", d => colorScale(d.value))
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`<strong>${d.tradition}</strong><br>${d.metric}: ${d.value.toFixed(3)}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition().duration(500).style("opacity", 0);
                });
            
            // Add title
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", -10)
                .attr("text-anchor", "middle")
                .style("font-size", "16px")
                .text("Ethical Analysis by Tradition and Metric");
            
            // Add legend
            const legendWidth = 300;
            const legendHeight = 40;
            
            const legendSvg = d3.select("#legend")
                .append("svg")
                .attr("width", legendWidth)
                .attr("height", legendHeight);
            
            const defs = legendSvg.append("defs");
            
            const linearGradient = defs.append("linearGradient")
                .attr("id", "linear-gradient");
            
            linearGradient
                .attr("x1", "0%")
                .attr("y1", "0%")
                .attr("x2", "100%")
                .attr("y2", "0%");
            
            // Set the color for the start (0%)
            linearGradient.append("stop")
                .attr("offset", "0%")
                .attr("stop-color", colorScale(0));
            
            // Set the color for the end (100%)
            linearGradient.append("stop")
                .attr("offset", "100%")
                .attr("stop-color", colorScale(d3.max(heatmapData, d => d.value)));
            
            // Draw the rectangle and fill with gradient
            legendSvg.append("rect")
                .attr("width", legendWidth)
                .attr("height", 20)
                .style("fill", "url(#linear-gradient)");
            
            // Create scale for legend
            const legendScale = d3.scaleLinear()
                .domain([0, d3.max(heatmapData, d => d.value)])
                .range([0, legendWidth]);
            
            // Add axis to legend
            const legendAxis = d3.axisBottom(legendScale)
                .ticks(5);
            
            legendSvg.append("g")
                .attr("transform", "translate(0,20)")
                .call(legendAxis);
            
            // Add legend title
            legendSvg.append("text")
                .attr("x", legendWidth / 2)
                .attr("y", legendHeight - 5)
                .attr("text-anchor", "middle")
                .style("font-size", "12px")
                .text("Metric Value (Higher = More Concern)");
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_intersectional_visualization(self) -> str:
        """
        Generate visualization for intersectional analysis results
        """
        filename = f"{self.output_dir}/intersectional_analysis.html"
        
        # Extract intersectional analysis data
        intersectional_data = {}
        if "intersectional_analysis" in self.results:
            for key, value in self.results["intersectional_analysis"].items():
                if isinstance(value, dict) and "max_accuracy_disparity" in value:
                    intersectional_data[key] = {
                        "max_accuracy_disparity": value["max_accuracy_disparity"],
                        "max_selection_disparity": value["max_selection_disparity"]
                    }
        
        # Generate HTML with interactive bubble chart using D3.js
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Intersectional Analysis</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .bubble { opacity: 0.7; }
                .bubble:hover { opacity: 1; stroke: #000; stroke-width: 1px; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .axis-label { font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="title">Intersectional Analysis: Disparity by Attribute Combination</div>
            <div id="bubble-chart"></div>
            
            <script>
            // Data from Python analysis
            const intersectionalData = """ + json.dumps(intersectional_data) + """;
            
            // Process data for bubble chart
            const bubbleData = Object.keys(intersectionalData).map(key => ({
                id: key,
                x: intersectionalData[key].max_accuracy_disparity,
                y: intersectionalData[key].max_selection_disparity,
                size: (intersectionalData[key].max_accuracy_disparity + 
                      intersectionalData[key].max_selection_disparity) / 2
            }));
            
            // Set up dimensions
            const margin = {top: 50, right: 50, bottom: 70, left: 80};
            const width = 700 - margin.left - margin.right;
            const height = 500 - margin.top - margin.bottom;
            
            // Create SVG
            const svg = d3.select("#bubble-chart")
                .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Create scales
            const x = d3.scaleLinear()
                .domain([0, d3.max(bubbleData, d => d.x) * 1.1])
                .range([0, width]);
            
            const y = d3.scaleLinear()
                .domain([0, d3.max(bubbleData, d => d.y) * 1.1])
                .range([height, 0]);
            
            const size = d3.scaleLinear()
                .domain([0, d3.max(bubbleData, d => d.size)])
                .range([10, 50]);
            
            const color = d3.scaleSequential()
                .domain([0, d3.max(bubbleData, d => d.size)])
                .interpolator(d3.interpolateReds);
            
            // Add x axis
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x));
            
            // Add x axis label
            svg.append("text")
                .attr("class", "axis-label")
                .attr("text-anchor", "middle")
                .attr("x", width / 2)
                .attr("y", height + margin.bottom - 10)
                .text("Accuracy Disparity");
            
            // Add y axis
            svg.append("g")
                .call(d3.axisLeft(y));
            
            // Add y axis label
            svg.append("text")
                .attr("class", "axis-label")
                .attr("text-anchor", "middle")
                .attr("transform", "rotate(-90)")
                .attr("x", -height / 2)
                .attr("y", -margin.left + 20)
                .text("Selection Rate Disparity");
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Add bubbles
            svg.selectAll("circle")
                .data(bubbleData)
                .enter()
                .append("circle")
                .attr("class", "bubble")
                .attr("cx", d => x(d.x))
                .attr("cy", d => y(d.y))
                .attr("r", d => size(d.size))
                .attr("fill", d => color(d.size))
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`<strong>${d.id}</strong><br>` +
                                 `Accuracy Disparity: ${d.x.toFixed(3)}<br>` + 
                                 `Selection Disparity: ${d.y.toFixed(3)}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition().duration(500).style("opacity", 0);
                });
            
            // Add labels to bubbles
            svg.selectAll("text.bubble-label")
                .data(bubbleData)
                .enter()
                .append("text")
                .attr("class", "bubble-label")
                .attr("x", d => x(d.x))
                .attr("y", d => y(d.y) - size(d.size) - 5)
                .attr("text-anchor", "middle")
                .style("font-size", "11px")
                .text(d => d.id);
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_metric_comparison_chart(self) -> str:
        """
        Generate a radar/spider chart comparing metrics across sensitive attributes
        """
        filename = f"{self.output_dir}/metric_comparison_radar.html"
        
        # Extract metrics for each sensitive attribute
        attribute_metrics = {}
        sensitive_attributes = self.results.get("metadata", {}).get("attributes_analyzed", [])
        
        for attribute in sensitive_attributes:
            attribute_metrics[attribute] = {}
            
            # Collect metrics from Western analysis
            if "tradition_analysis" in self.results and "western" in self.results["tradition_analysis"]:
                western = self.results["tradition_analysis"]["western"]
                for metric, results in western.items():
                    for key, value in results.items():
                        if attribute in key and isinstance(value, (int, float)):
                            attribute_metrics[attribute][f"western_{metric}"] = value
            
            # Collect metrics from Ubuntu analysis
            if "tradition_analysis" in self.results and "ubuntu" in self.results["tradition_analysis"]:
                ubuntu = self.results["tradition_analysis"]["ubuntu"]
                for metric, results in ubuntu.items():
                    for key, value in results.items():
                        if attribute in key and isinstance(value, (int, float)):
                            attribute_metrics[attribute][f"ubuntu_{metric}"] = value
            
            # Add other traditions as needed
        
        # Generate HTML with interactive radar chart using Chart.js
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Metric Comparison by Attribute</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-radar"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 800px; height: 600px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .attribute-selector { text-align: center; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="title">Metric Comparison by Sensitive Attribute</div>
            <div class="attribute-selector">
                <label for="attribute-select">Select Attribute: </label>
                <select id="attribute-select"></select>
            </div>
            <div class="chart-container">
                <canvas id="radar-chart"></canvas>
            </div>
            
            <script>
            // Data from Python analysis
            const attributeMetrics = """ + json.dumps(attribute_metrics) + """;
            const attributes = Object.keys(attributeMetrics);
            
            // Set up attribute selector
            const select = document.getElementById('attribute-select');
            attributes.forEach(attr => {
                const option = document.createElement('option');
                option.value = attr;
                option.text = attr;
                select.appendChild(option);
            });
            
            // Set up chart
            const ctx = document.getElementById('radar-chart').getContext('2d');
            let radarChart;
            
            function updateChart(attribute) {
                // Get metrics for this attribute
                const metrics = attributeMetrics[attribute];
                const metricNames = Object.keys(metrics);
                
                // Process data for radar chart
                const data = {
                    labels: metricNames,
                    datasets: [{
                        label: attribute,
                        data: metricNames.map(m => metrics[m]),
                        fill: true,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgb(54, 162, 235)',
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(54, 162, 235)'
                    }]
                };
                
                // Destroy previous chart if it exists
                if (radarChart) {
                    radarChart.destroy();
                }
                
                // Create new chart
                radarChart = new Chart(ctx, {
                    type: 'radar',
                    data: data,
                    options: {
                        elements: {
                            line: {
                                borderWidth: 3
                            }
                        },
                        scales: {
                            r: {
                                angleLines: {
                                    display: true
                                },
                                suggestedMin: 0,
                                suggestedMax: Math.max(...Object.values(metrics)) * 1.2
                            }
                        }
                    }
                });
            }
            
            // Set up event listener for attribute selector
            select.addEventListener('change', function() {
                updateChart(this.value);
            });
            
            // Initialize chart with first attribute
            if (attributes.length > 0) {
                updateChart(attributes[0]);
            }
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_recommendation_dashboard(self) -> str:
        """
        Generate interactive dashboard for recommendations
        """
        filename = f"{self.output_dir}/recommendation_dashboard.html"
        
        # Extract recommendations
        recommendations = {}
        if "recommendations" in self.results:
            for category, recs in self.results["recommendations"].items():
                if category != "priority_issues" and isinstance(recs, list):
                    recommendations[category] = recs
        
        # Extract priority issues
        priority_issues = []
        if "recommendations" in self.results and "priority_issues" in self.results["recommendations"]:
            priority_issues = self.results["recommendations"]["priority_issues"]
        
        # Generate HTML with interactive dashboard
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Recommendation Dashboard</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .dashboard { display: flex; flex-wrap: wrap; }
                .panel { 
                    flex: 1; 
                    min-width: 300px; 
                    margin: 10px; 
                    padding: 15px; 
                    background-color: #f9f9f9; 
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .panel h2 { font-size: 16px; margin-top: 0; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
                .recommendation { padding: 8px; margin: 5px 0; background-color: #fff; border-radius: 3px; }
                .priority { background-color: #fff0f0; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .priority-issues { margin-bottom: 20px; }
                .chart-container { margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="title">Ethical Analysis Recommendations</div>
            
            <div class="priority-issues panel">
                <h2>Priority Issues</h2>
                <div id="priority-list"></div>
                <div class="chart-container">
                    <svg id="priority-chart" width="100%" height="200"></svg>
                </div>
            </div>
            
            <div class="dashboard">
                <!-- Recommendation panels will be added here -->
            </div>
            
            <script>
            // Data from Python analysis
            const recommendations = """ + json.dumps(recommendations) + """;
            const priorityIssues = """ + json.dumps(priority_issues) + """;
            
            // Create recommendation panels
            const dashboard = document.querySelector('.dashboard');
            Object.keys(recommendations).forEach(category => {
                const panel = document.createElement('div');
                panel.className = 'panel';
                
                const title = document.createElement('h2');
                title.textContent = category.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                panel.appendChild(title);
                
                recommendations[category].forEach(rec => {
                    const recommendation = document.createElement('div');
                    recommendation.className = 'recommendation';
                    recommendation.textContent = rec;
                    panel.appendChild(recommendation);
                });
                
                dashboard.appendChild(panel);
            });
            
            // Create priority issues list
            const priorityList = document.getElementById('priority-list');
            priorityIssues.forEach(issue => {
                const item = document.createElement('div');
                item.className = 'recommendation priority';
                item.textContent = `${issue.tradition} - ${issue.metric}: ${issue.issue} (Severity: ${issue.severity.toFixed(2)})`;
                priorityList.appendChild(item);
            });
            
            // Create priority issues chart
            if (priorityIssues.length > 0) {
                const svg = d3.select("#priority-chart");
                const margin = {top: 20, right: 30, bottom: 40, left: 40};
                const width = parseInt(svg.style('width')) - margin.left - margin.right;
                const height = 200 - margin.top - margin.bottom;
                
                const g = svg.append("g")
                    .attr("transform", `translate(${margin.left},${margin.top})`);
                
                // Create x scale
                const x = d3.scaleBand()
                    .domain(priorityIssues.map(d => d.issue.split('_').pop()))
                    .range([0, width])
                    .padding(0.1);
                
                // Create y scale
                const y = d3.scaleLinear()
                    .domain([0, d3.max(priorityIssues, d => d.severity)])
                    .nice()
                    .range([height, 0]);
                
                // Add bars
                g.selectAll(".bar")
                    .data(priorityIssues)
                    .enter().append("rect")
                    .attr("class", "bar")
                    .attr("x", d => x(d.issue.split('_').pop()))
                    .attr("y", d => y(d.severity))
                    .attr("width", x.bandwidth())
                    .attr("height", d => height - y(d.severity))
                    .attr("fill", d => d3.interpolateReds(d.severity / d3.max(priorityIssues, d => d.severity)));
                
                // Add x axis
                g.append("g")
                    .attr("transform", `translate(0,${height})`)
                    .call(d3.axisBottom(x))
                    .selectAll("text")
                    .attr("transform", "rotate(-45)")
                    .style("text-anchor", "end");
                
                // Add y axis
                g.append("g")
                    .call(d3.axisLeft(y).ticks(5));
                
                // Add y axis label
                g.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("y", -margin.left)
                    .attr("x", -height / 2)
                    .attr("dy", "1em")
                    .style("text-anchor", "middle")
                    .style("font-size", "12px")
                    .text("Severity");
            }
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_cultural_inclusion_visualization(self) -> str:
        """
        Generate visualization for cultural inclusion index
        """
        filename = f"{self.output_dir}/cultural_inclusion.html"
        
        # Extract cultural inclusion data
        inclusion_data = {}
        if "integrated_analysis" in self.results and "cultural_inclusion_index" in self.results["integrated_analysis"]:
            inclusion_data = self.results["integrated_analysis"]["cultural_inclusion_index"]
        
        # Generate HTML with gauge charts
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Cultural Inclusion Index</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/d3-gauge@0.6.0/dist/d3-gauge.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .gauges-container { display: flex; flex-wrap: wrap; justify-content: center; }
                .gauge-wrapper { margin: 15px; text-align: center; }
                .gauge-title { font-size: 14px; margin-top: 10px; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .overall-score { font-size: 24px; text-align: center; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="title">Cultural Inclusion Index by Attribute</div>
            
            <div class="overall-score" id="overall-score"></div>
            
            <div class="gauges-container" id="gauges"></div>
            
            <script>
            // Data from Python analysis
            const inclusionData = """ + json.dumps(inclusion_data) + """;
            
            // Create overall score display
            if (inclusionData.overall_inclusion) {
                const scoreElem = document.getElementById('overall-score');
                const score = inclusionData.overall_inclusion;
                scoreElem.innerHTML = `Overall Cultural Inclusion Score: <strong>${(score * 100).toFixed(1)}%</strong>`;
                scoreElem.style.color = score > 0.7 ? '#2c7bb6' : score > 0.5 ? '#fdae61' : '#d7191c';
            }
            
            // Create gauge for each attribute
            const gaugeContainer = document.getElementById('gauges');
            Object.keys(inclusionData).forEach(key => {
                if (key.startsWith('cultural_inclusion_')) {
                    const attribute = key.replace('cultural_inclusion_', '');
                    const score = inclusionData[key];
                    
                    // Create wrapper for this gauge
                    const wrapper = document.createElement('div');
                    wrapper.className = 'gauge-wrapper';
                    
                    // Create gauge element
                    const gaugeElem = document.createElement('div');
                    gaugeElem.id = `gauge-${attribute}`;
                    wrapper.appendChild(gaugeElem);
                    
                    // Create title
                    const title = document.createElement('div');
                    title.className = 'gauge-title';
                    title.textContent = attribute;
                    wrapper.appendChild(title);
                    
                    gaugeContainer.appendChild(wrapper);
                    
                    // Create gauge
                    const gauge = d3.gauge()
                        .width(200)
                        .height(200)
                        .min(0)
                        .max(1)
                        .value(score)
                        .backgroundColor("whitesmoke")
                        .transition(1000)
                        .thresholds([
                            {value: 0.3, color: "#d7191c"},
                            {value: 0.5, color: "#fdae61"},
                            {value: 0.7, color: "#abd9e9"},
                            {value: 1.0, color: "#2c7bb6"}
                        ]);
                    
                    d3.select(`#gauge-${attribute}`).call(gauge);
                }
            });
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_group_relationship_diagram(self) -> str:
        """
        Generate chord diagram to visualize relationships between groups
        """
        filename = f"{self.output_dir}/group_relationships.html"
        
        # Extract relationship data (simplified for example)
        relationship_data = []
        sensitive_attributes = self.results.get("metadata", {}).get("attributes_analyzed", [])
        
        # In a real implementation, this would extract actual relationship data
        # This is a placeholder to show the visualization structure
        if "tradition_analysis" in self.results and "ubuntu" in self.results["tradition_analysis"]:
            ubuntu_results = self.results["tradition_analysis"]["ubuntu"]
            if "group_harmony" in ubuntu_results:
                for attr in sensitive_attributes:
                    if f"impact_details_{attr}" in ubuntu_results["group_harmony"]:
                        impact_details = ubuntu_results["group_harmony"][f"impact_details_{attr}"]
                        groups = list(impact_details.keys())
                        
                        # Create matrix of relationships
                        matrix = []
                        for i in range(len(groups)):
                            row = []
                            for j in range(len(groups)):
                                if i == j:
                                    row.append(0)
                                else:
                                    # This would use actual relationship data in practice
                                    # This is a placeholder value
                                    row.append(impact_details[groups[i]].get("external_impact", 0.1) * 10)
                            matrix.append(row)
                        
                        relationship_data.append({
                            "attribute": attr,
                            "groups": groups,
                            "matrix": matrix
                        })
        
        # Generate HTML with chord diagram
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Group Relationships</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 800px; height: 600px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .attribute-selector { text-align: center; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="title">Group Relationships: Impact Analysis</div>
            <div class="attribute-selector">
                <label for="relationship-select">Select Attribute: </label>
                <select id="relationship-select"></select>
            </div>
            <div class="chart-container">
                <svg id="chord-diagram" width="800" height="600"></svg>
            </div>
            
            <script>
            // Data from Python analysis
            const relationshipData = """ + json.dumps(relationship_data) + """;
            
            // Set up attribute selector
            const select = document.getElementById('relationship-select');
            relationshipData.forEach((data, i) => {
                const option = document.createElement('option');
                option.value = i;
                option.text = data.attribute;
                select.appendChild(option);
            });
            
            // Function to create chord diagram
            function createChordDiagram(dataIndex) {
                const data = relationshipData[dataIndex];
                const svg = d3.select("#chord-diagram");
                svg.selectAll("*").remove();
                
                const width = 800;
                const height = 600;
                const outerRadius = Math.min(width, height) * 0.4;
                const innerRadius = outerRadius - 30;
                
                const chord = d3.chordDirected()
                    .padAngle(0.05)
                    .sortSubgroups(d3.descending)
                    (data.matrix);
                
                const arc = d3.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(outerRadius);
                
                const ribbon = d3.ribbonArrow()
                    .radius(innerRadius - 5)
                    .padAngle(1 / innerRadius);
                
                const color = d3.scaleOrdinal()
                    .domain(d3.range(data.groups.length))
                    .range(d3.schemeCategory10);
                
                const g = svg.append("g")
                    .attr("transform", `translate(${width/2},${height/2})`)
                    .datum(chord);
                
                // Create the groups
                const group = g.append("g")
                    .selectAll("g")
                    .data(d => d.groups)
                    .join("g");
                
                // Add arcs
                group.append("path")
                    .attr("fill", d => color(d.index))
                    .attr("stroke", "white")
                    .attr("d", arc);
                
                // Add labels
                group.append("text")
                    .each(d => { d.angle = (d.startAngle + d.endAngle) / 2; })
                    .attr("dy", ".35em")
                    .attr("transform", d => `
                        rotate(${(d.angle * 180 / Math.PI - 90)})
                        translate(${outerRadius + 10})
                        ${d.angle > Math.PI ? "rotate(180)" : ""}
                    `)
                    .attr("text-anchor", d => d.angle > Math.PI ? "end" : null)
                    .text(d => data.groups[d.index]);
                
                // Add ribbons
                g.append("g")
                    .selectAll("path")
                    .data(d => d)
                    .join("path")
                    .attr("fill", d => color(d.source.index))
                    .attr("fill-opacity", 0.7)
                    .attr("d", ribbon)
                    .append("title")
                    .text(d => `${data.groups[d.source.index]} → ${data.groups[d.target.index]}: ${d.source.value.toFixed(2)}`);
            }
            
            // Set up event listener for attribute selector
            select.addEventListener('change', function() {
                createChordDiagram(parseInt(this.value));
            });
            
            // Initialize with first attribute if available
            if (relationshipData.length > 0) {
                createChordDiagram(0);
            }
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename


class ReportGenerator:
    """
    Generates comprehensive PDF reports from ethical analysis results
    """
    
    def __init__(self, results: Dict[str, Any], visualization_generator: VisualizationGenerator = None):
        """
        Initialize with analysis results and optional visualization generator
        """
        self.results = results
        self.visualization_generator = visualization_generator
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8
        ))
    
    def generate_report(self, output_path: str = "ethical_analysis_report.pdf") -> str:
        """
        Generate comprehensive PDF report
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create content elements
        elements = []
        
        # Add title
        elements.append(Paragraph("Ethical Analysis Report", self.styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated: {timestamp}", self.styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Add executive summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionTitle']))
        elements.append(self._create_executive_summary())
        elements.append(Spacer(1, 12))
        
        # Add metadata
        elements.append(Paragraph("Analysis Metadata", self.styles['SectionTitle']))
        elements.append(self._create_metadata_table())
        elements.append(Spacer(1, 24))
        
        # Add priority issues
        elements.append(Paragraph("Priority Issues", self.styles['SectionTitle']))
        elements.extend(self._create_priority_issues_section())
        elements.append(Spacer(1, 24))
        
        # Add ethical tradition analysis
        elements.append(Paragraph("Ethical Tradition Analysis", self.styles['SectionTitle']))
        elements.extend(self._create_tradition_analysis_section())
        elements.append(Spacer(1, 24))
        
        # Add intersectional analysis
        elements.append(Paragraph("Intersectional Analysis", self.styles['SectionTitle']))
        elements.extend(self._create_intersectional_analysis_section())
        elements.append(Spacer(1, 24))
        
        # Add integrated analysis
        elements.append(Paragraph("Integrated Ethical Analysis", self.styles['SectionTitle']))
        elements.extend(self._create_integrated_analysis_section())
        elements.append(Spacer(1, 24))
        
        # Add recommendations
        elements.append(Paragraph("Recommendations", self.styles['SectionTitle']))
        elements.extend(self._create_recommendations_section())
        elements.append(Spacer(1, 24))
        
        # Add visualizations if available
        if self.visualization_generator:
            elements.append(Paragraph("Visualizations", self.styles['SectionTitle']))
            elements.extend(self._create_visualizations_section())
            elements.append(Spacer(1, 24))
        
        # Build document
        doc.build(elements)
        
        return output_path
    
    def _create_executive_summary(self) -> Paragraph:
        """
        Create executive summary of findings
        """
        # In a real implementation, this would generate a dynamic summary based on results
        
        summary_text = """
        This report presents the findings from a comprehensive ethical analysis of the dataset 
        using multiple ethical frameworks including Western and non-Western perspectives. 
        The analysis identified several key issues related to bias and cultural representation 
        that require attention. These issues vary in severity and impact across different 
        demographic groups. The most significant concerns relate to disparities in selection rates 
        and accuracy across intersectional identities. This report provides detailed analysis 
        and specific recommendations for addressing these issues.
        """
        
        return Paragraph(summary_text, self.styles['Normal'])
    
    def _create_metadata_table(self) -> Table:
        """
        Create table with analysis metadata
        """
        metadata = self.results.get("metadata", {})
        
        data = [
            ["Dataset Size", str(metadata.get("dataset_size", "N/A"))],
            ["Attributes Analyzed", ", ".join(metadata.get("attributes_analyzed", ["N/A"]))],
            ["Domain Context", metadata.get("domain_context", "N/A")],
            ["Ethical Traditions", ", ".join(self._get_ethical_traditions())]
        ]
        
        table = Table(data, colWidths=[150, 300])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        return table
    
    def _get_ethical_traditions(self) -> List[str]:
        """
        Get list of ethical traditions used in analysis
        """
        if "tradition_analysis" in self.results:
            return list(self.results["tradition_analysis"].keys())
        return ["N/A"]
    
    def _create_priority_issues_section(self) -> List:
        """
        Create section for priority issues
        """
        elements = []
        
        if "recommendations" in self.results and "priority_issues" in self.results["recommendations"]:
            priority_issues = self.results["recommendations"]["priority_issues"]
            
            if priority_issues:
                # Create table for priority issues
                table_data = [["Ethical Tradition", "Metric", "Issue", "Severity"]]
                
                for issue in priority_issues:
                    table_data.append([
                        issue.get("tradition", ""),
                        issue.get("metric", ""),
                        issue.get("issue", ""),
                        f"{issue.get('severity', 0):.2f}"
                    ])
                
                table = Table(table_data, colWidths=[100, 100, 200, 50])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('PADDING', (0, 0), (-1, -1), 6)
                ]))
                
                elements.append(table)
            else:
                elements.append(Paragraph("No priority issues identified.", self.styles['Normal']))
        else:
            elements.append(Paragraph("No priority issues data available.", self.styles['Normal']))
        
        return elements
    
    def _create_tradition_analysis_section(self) -> List:
        """
        Create section for ethical tradition analysis
        """
        elements = []
        
        if "tradition_analysis" in self.results:
            tradition_analysis = self.results["tradition_analysis"]
            
            for tradition, metrics in tradition_analysis.items():
                elements.append(Paragraph(f"{tradition.capitalize()} Analysis", self.styles['SubsectionTitle']))
                
                for metric_name, results in metrics.items():
                    elements.append(Paragraph(f"{metric_name.replace('_', ' ').capitalize()}", self.styles['Italic']))
                    
                    # Create table for this metric
                    table_data = []
                    for key, value in results.items():
                        if isinstance(value, (int, float)):
                            table_data.append([key, f"{value:.3f}"])
                    
                    if table_data:
                        table = Table(table_data, colWidths=[250, 100])
                        table.setStyle(TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('PADDING', (0, 0), (-1, -1), 4)
                        ]))
                        
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                    else:
                        elements.append(Paragraph("No numeric results available.", self.styles['Normal']))
                        elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No tradition analysis data available.", self.styles['Normal']))
        
        return elements
    
    def _create_intersectional_analysis_section(self) -> List:
        """
        Create section for intersectional analysis
        """
        elements = []
        
        if "intersectional_analysis" in self.results:
            intersectional_analysis = self.results["intersectional_analysis"]
            
            if isinstance(intersectional_analysis, dict) and intersectional_analysis:
                table_data = [["Attribute Intersection", "Accuracy Disparity", "Selection Disparity"]]
                
                for key, value in intersectional_analysis.items():
                    if isinstance(value, dict) and "max_accuracy_disparity" in value:
                        table_data.append([
                            key,
                            f"{value['max_accuracy_disparity']:.3f}",
                            f"{value['max_selection_disparity']:.3f}"
                        ])
                
                if len(table_data) > 1:
                    table = Table(table_data, colWidths=[200, 150, 150])
                    table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('PADDING', (0, 0), (-1, -1), 6)
                    ]))
                    
                    elements.append(table)
                    elements.append(Spacer(1, 12))
                    
                    # Add interpretation
                    interpretation = """
                    Intersectional analysis examines how multiple sensitive attributes combine to create 
                    unique patterns of bias. Higher disparity values indicate greater differences in treatment 
                    between different intersectional groups, which may require specific mitigation strategies.
                    """
                    elements.append(Paragraph(interpretation, self.styles['Normal']))
                else:
                    elements.append(Paragraph("No intersectional disparities data available.", self.styles['Normal']))
            else:
                elements.append(Paragraph("No intersectional analysis data available.", self.styles['Normal']))
        else:
            elements.append(Paragraph("No intersectional analysis data available.", self.styles['Normal']))
        
        return elements
    
    def _create_integrated_analysis_section(self) -> List:
        """
        Create section for integrated ethical analysis
        """
        elements = []
        
        if "integrated_analysis" in self.results:
            integrated_analysis = self.results["integrated_analysis"]
            
            for metric_name, results in integrated_analysis.items():
                elements.append(Paragraph(f"{metric_name.replace('_', ' ').capitalize()}", self.styles['SubsectionTitle']))
                
                if isinstance(results, dict):
                    table_data = []
                    for key, value in results.items():
                        if isinstance(value, (int, float)):
                            table_data.append([key, f"{value:.3f}"])
                    
                    if table_data:
                        table = Table(table_data, colWidths=[250, 100])
                        table.setStyle(TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('PADDING', (0, 0), (-1, -1), 4)
                        ]))
                        
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                else:
                    elements.append(Paragraph(f"Result: {results}", self.styles['Normal']))
                    elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No integrated analysis data available.", self.styles['Normal']))
        
        return elements
    
    def _create_recommendations_section(self) -> List:
        """
        Create section for recommendations
        """
        elements = []
        
        if "recommendations" in self.results:
            recommendations = self.results["recommendations"]
            
            for category, recs in recommendations.items():
                if category != "priority_issues" and isinstance(recs, list) and recs:
                    elements.append(Paragraph(f"{category.replace('_', ' ').capitalize()}", self.styles['SubsectionTitle']))
                    
                    for i, rec in enumerate(recs):
                        elements.append(Paragraph(f"{i+1}. {rec}", self.styles['Normal']))
                    
                    elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No recommendations data available.", self.styles['Normal']))
        
        return elements
    
    def _create_visualizations_section(self) -> List:
        """
        Create section with visualizations
        """
        elements = []
        
        # This would ideally integrate the visualizations directly
        # For simplicity, we'll just reference them
        elements.append(Paragraph(
            "Interactive visualizations have been generated and are available in the 'visualizations' directory. "
            "These visualizations provide detailed insights into the ethical analysis findings.",
            self.styles['Normal']
        ))
        
        return elements


def run_full_analysis_with_visualizations(
    dataset_path: str,
    sensitive_attributes: List[str],
    prediction_column: str,
    actual_column: str,
    output_dir: str = "ethical_analysis_output"
):
    """
    Complete function to run full analysis with visualizations and report
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    viz_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # Load dataset
    dataset = pd.read_csv(dataset_path)
    
    # Initialize framework with cultural contexts
    cultural_contexts = {
        "ubuntu": {
            "harmony_threshold": 0.7,
            "community_values": ["solidarity", "respect", "compassion"]
        },
        "confucian": {
            "relationship_priorities": ["family", "community", "society"]
        }
    }
    
    # Historical context about past discrimination
    historical_context = {
        "race": {
            "Black": 1.5,  # Higher factor due to historical discrimination
            "Hispanic": 1.3,
            "White": 1.0,
            "Asian": 1.1
        },
        "gender": {
            "Female": 1.3,
            "Male": 1.0,
            "Non-binary": 1.2
        }
    }
    
    # Initialize framework
    framework = DualEthicsFramework(
        cultural_context=cultural_contexts,
        historical_context=historical_context
    )
    
    # Run analysis
    results = framework.analyze_dataset(
        dataset=dataset,
        sensitive_attributes=sensitive_attributes,
        prediction_column=prediction_column,
        actual_column=actual_column
    )
    
    # Generate visualizations
    viz_generator = VisualizationGenerator(results, output_dir=viz_dir)
    visualizations = viz_generator.generate_all_visualizations()
    
    # Generate report
    report_generator = ReportGenerator(results, viz_generator)
    report_path = os.path.join(output_dir, "ethical_analysis_report.pdf")
    report_generator.generate_report(report_path)
    
    return {
        "results": results,
        "visualizations": visualizations,
        "report": report_path
    }


# Suggested platform names
PLATFORM_NAMES = [
    "EthiViz - Cultural Bias Analysis Platform",
    "HarmonyLens - Cross-Cultural AI Ethics Framework",
    "PerspectAI - Multi-Perspective Dataset Analysis System"
]

# Print suggested names
if __name__ == "__main__":
    print("Suggested Platform Names:")
    for i, name in enumerate(PLATFORM_NAMES, 1):
        print(f"{i}. {name}")