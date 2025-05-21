import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from datetime import datetime

class ImageVisualizationGenerator:
    """
    Generates visualizations for image analysis results,
    focusing on cultural bias aspects across multiple ethical frameworks.
    """
    
    def __init__(self, analysis_results: Dict[str, Any], output_dir: str = "image_visualizations"):
        """
        Initialize with analysis results and output directory
        
        Parameters:
        -----------
        analysis_results : Dict[str, Any]
            Results from image analysis, containing individual and aggregated results
        
        output_dir : str
            Directory to save visualizations
        """
        self.results = analysis_results
        self.output_dir = output_dir
        self.visualization_files = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all_visualizations(self) -> Dict[str, str]:
        """
        Generate all visualizations for image analysis results
        
        Returns:
        --------
        Dict[str, str]
            Dictionary mapping visualization names to file paths
        """
        visualizations = {}
        
        # Generate skin tone distribution visualization
        visualizations["skin_tone_distribution"] = self.generate_skin_tone_visualization()
        
        # Generate color distribution visualization
        visualizations["color_distribution"] = self.generate_color_distribution_visualization()
        
        # Generate gender representation visualization
        visualizations["gender_representation"] = self.generate_gender_visualization()
        
        # Generate age representation visualization
        visualizations["age_representation"] = self.generate_age_visualization()
        
        # Generate cultural elements visualization
        visualizations["cultural_elements"] = self.generate_cultural_elements_visualization()
        
        # Generate bias index visualization
        visualizations["bias_index"] = self.generate_bias_index_visualization()
        
        return visualizations
    
    def generate_skin_tone_visualization(self) -> str:
        """
        Generate visualization for skin tone distribution
        """
        filename = f"{self.output_dir}/skin_tone_distribution.html"
        
        # Extract skin tone data from aggregated results
        skin_tone_data = self.results.get("aggregated_results", {}).get("skin_tone_distribution", {})
        
        # Create HTML content with D3.js visualization
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Skin Tone Distribution</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 800px; height: 400px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
                .bar { fill: steelblue; }
                .bar:hover { fill: #5599ff; }
                .axis-label { font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="title">Skin Tone Distribution in Dataset Images</div>
            <div class="chart-container">
                <svg id="chart" width="800" height="400"></svg>
            </div>
            <div class="footnote">Based on simplified Fitzpatrick scale approximation</div>
            
            <script>
            // Data from Python analysis
            const skinToneData = """ + json.dumps(skin_tone_data) + """;
            
            // Process data for visualization
            const data = Object.entries(skinToneData)
                .filter(([key, _]) => key !== 'estimation_confidence')
                .map(([key, value]) => ({
                    category: key.replace('type_', 'Type '),
                    value: value
                }));
            
            // Set up dimensions
            const margin = {top: 40, right: 20, bottom: 60, left: 60};
            const width = 800 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            // Create SVG
            const svg = d3.select("#chart")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Create x scale
            const x = d3.scaleBand()
                .range([0, width])
                .domain(data.map(d => d.category))
                .padding(0.2);
            
            // Create y scale
            const y = d3.scaleLinear()
                .domain([0, Math.max(...data.map(d => d.value), 0.1)])
                .nice()
                .range([height, 0]);
            
            // Create skin tone color scale for bars
            const colorScale = d3.scaleOrdinal()
                .domain(data.map(d => d.category))
                .range(['#ffdbbc', '#f6cfb0', '#e4b59e', '#c68c6d', '#8d5524', '#462a16']);
            
            // Add x axis
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .attr("transform", "rotate(-45)")
                .style("text-anchor", "end");
            
            // Add x axis label
            svg.append("text")
                .attr("class", "axis-label")
                .attr("text-anchor", "middle")
                .attr("x", width / 2)
                .attr("y", height + margin.bottom - 10)
                .text("Skin Tone Category");
            
            // Add y axis
            svg.append("g")
                .call(d3.axisLeft(y));
            
            // Add y axis label
            svg.append("text")
                .attr("class", "axis-label")
                .attr("text-anchor", "middle")
                .attr("transform", "rotate(-90)")
                .attr("x", -height / 2)
                .attr("y", -margin.left + 15)
                .text("Proportion in Dataset");
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Add bars
            svg.selectAll(".bar")
                .data(data)
                .join("rect")
                .attr("class", "bar")
                .attr("x", d => x(d.category))
                .attr("y", d => y(d.value))
                .attr("width", x.bandwidth())
                .attr("height", d => height - y(d.value))
                .attr("fill", d => colorScale(d.category))
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`${d.category}<br>${(d.value * 100).toFixed(1)}%`)
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
                .text("Skin Tone Distribution");
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_color_distribution_visualization(self) -> str:
        """
        Generate visualization for color distribution
        """
        filename = f"{self.output_dir}/color_distribution.html"
        
        # Extract color data from aggregated results
        color_data = self.results.get("aggregated_results", {}).get("color_distribution", {})
        
        # Create HTML content with D3.js visualization
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Color Distribution</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 700px; height: 500px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
            </style>
        </head>
        <body>
            <div class="title">Color Distribution in Dataset Images</div>
            <div class="chart-container">
                <svg id="pie-chart" width="700" height="500"></svg>
            </div>
            <div class="footnote">Colors represent the dominant colors in the analyzed images</div>
            
            <script>
            // Data from Python analysis
            const colorData = """ + json.dumps(color_data) + """;
            
            // Process data for visualization
            const data = Object.entries(colorData)
                .map(([key, value]) => ({
                    color: key,
                    value: value
                }))
                .filter(d => d.value > 0); // Only show colors that appear
            
            // Set up dimensions
            const width = 700;
            const height = 500;
            const radius = Math.min(width, height) / 2 - 40;
            
            // Create SVG
            const svg = d3.select("#pie-chart")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", `translate(${width/2},${height/2})`);
            
            // Create color scale
            const colorScale = d3.scaleOrdinal()
                .domain(data.map(d => d.color))
                .range({
                    'red': '#e41a1c',
                    'green': '#4daf4a',
                    'blue': '#377eb8',
                    'yellow': '#ffff33',
                    'cyan': '#41b6c4',
                    'magenta': '#984ea3',
                    'white': '#f0f0f0',
                    'black': '#333333'
                });
                
            // Create pie generator
            const pie = d3.pie()
                .value(d => d.value)
                .sort(null);
            
            // Create arc generator
            const arc = d3.arc()
                .innerRadius(0)
                .outerRadius(radius);
            
            // Create outer arc for labels
            const outerArc = d3.arc()
                .innerRadius(radius * 1.1)
                .outerRadius(radius * 1.1);
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Create pie slices
            const slices = svg.selectAll(".slice")
                .data(pie(data))
                .enter()
                .append("g")
                .attr("class", "slice");
            
            // Add path (slice)
            slices.append("path")
                .attr("d", arc)
                .attr("fill", d => d.data.color)
                .style("opacity", 0.8)
                .style("stroke", "white")
                .style("stroke-width", 2)
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`${d.data.color}<br>${(d.data.value * 100).toFixed(1)}%`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition().duration(500).style("opacity", 0);
                });
            
            // Add labels
            const text = svg.selectAll(".label")
                .data(pie(data))
                .enter()
                .append("text")
                .attr("class", "label")
                .attr("dy", ".35em");
            
            text.append("tspan")
                .attr("x", 0)
                .text(d => d.data.color);
            
            text.append("tspan")
                .attr("x", 0)
                .attr("dy", "1.2em")
                .text(d => `${(d.data.value * 100).toFixed(1)}%`);
            
            text.attr("transform", function(d) {
                const pos = outerArc.centroid(d);
                const midAngle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                pos[0] = radius * 0.7 * (midAngle < Math.PI ? 1 : -1);
                return `translate(${pos})`;
            })
            .style("text-anchor", function(d) {
                const midAngle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                return midAngle < Math.PI ? "start" : "end";
            });
            
            // Add polylines
            svg.selectAll(".line")
                .data(pie(data))
                .enter()
                .append("polyline")
                .attr("points", function(d) {
                    const pos = outerArc.centroid(d);
                    const midAngle = d.startAngle + (d.endAngle - d.startAngle) / 2;
                    pos[0] = radius * 0.7 * (midAngle < Math.PI ? 1 : -1);
                    return [arc.centroid(d), outerArc.centroid(d), pos];
                })
                .style("fill", "none")
                .style("stroke", "#999")
                .style("stroke-width", 1);
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_gender_visualization(self) -> str:
        """
        Generate visualization for gender representation
        """
        filename = f"{self.output_dir}/gender_representation.html"
        
        # Extract gender data from aggregated results
        gender_data = self.results.get("aggregated_results", {}).get("gender_representation", {})
        
        # Filter out the estimation_confidence field
        if "estimation_confidence" in gender_data:
            confidence = gender_data["estimation_confidence"]
            gender_data = {k: v for k, v in gender_data.items() if k != "estimation_confidence"}
        else:
            confidence = "unknown"
        
        # Create HTML content with D3.js visualization
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Gender Representation</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 700px; height: 400px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
                .confidence-note { font-size: 14px; text-align: center; margin-top: 10px; color: #d62728; }
                .segment { stroke: white; stroke-width: 2; }
                .segment:hover { opacity: 0.8; }
                .label { font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="title">Gender Representation in Dataset Images</div>
            <div class="chart-container">
                <svg id="donut-chart" width="700" height="400"></svg>
            </div>
            <div class="confidence-note">Estimation confidence: """ + confidence + """</div>
            <div class="footnote">Note: Gender estimation is approximate and should be validated with human review</div>
            
            <script>
            // Data from Python analysis
            const genderData = """ + json.dumps(gender_data) + """;
            
            // Process data for visualization
            const data = Object.entries(genderData)
                .map(([key, value]) => ({
                    category: key,
                    value: value
                }))
                .filter(d => d.value > 0); // Only show categories that appear
            
            // Set up dimensions
            const width = 700;
            const height = 400;
            const radius = Math.min(width, height) / 2 - 40;
            
            // Create SVG
            const svg = d3.select("#donut-chart")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", `translate(${width/2},${height/2})`);
            
            // Create color scale
            const colorScale = d3.scaleOrdinal()
                .domain(data.map(d => d.category))
                .range(d3.schemeSet2);
            
            // Create pie generator
            const pie = d3.pie()
                .value(d => d.value)
                .sort(null);
            
            // Create arc generator for donut
            const arc = d3.arc()
                .innerRadius(radius * 0.5) // Make it a donut chart
                .outerRadius(radius);
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Create donut segments
            svg.selectAll(".segment")
                .data(pie(data))
                .enter()
                .append("path")
                .attr("class", "segment")
                .attr("d", arc)
                .attr("fill", d => colorScale(d.data.category))
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`${d.data.category}<br>${(d.data.value * 100).toFixed(1)}%`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition().duration(500).style("opacity", 0);
                });
            
            // Add labels
            svg.selectAll(".label")
                .data(pie(data))
                .enter()
                .append("text")
                .attr("class", "label")
                .attr("transform", d => {
                    const centroid = arc.centroid(d);
                    return `translate(${centroid})`;
                })
                .attr("dy", "0.35em")
                .attr("text-anchor", "middle")
                .text(d => `${d.data.category}: ${(d.data.value * 100).toFixed(0)}%`);
            
            // Add center text
            svg.append("text")
                .attr("text-anchor", "middle")
                .attr("dy", "-0.5em")
                .style("font-size", "16px")
                .text("Gender");
            
            svg.append("text")
                .attr("text-anchor", "middle")
                .attr("dy", "1em")
                .style("font-size", "14px")
                .text("Distribution");
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_age_visualization(self) -> str:
        """
        Generate visualization for age representation
        """
        filename = f"{self.output_dir}/age_representation.html"
        
        # Extract age data from aggregated results
        age_data = self.results.get("aggregated_results", {}).get("age_representation", {})
        
        # Filter out the estimation_confidence field
        if "estimation_confidence" in age_data:
            confidence = age_data["estimation_confidence"]
            age_data = {k: v for k, v in age_data.items() if k != "estimation_confidence"}
        else:
            confidence = "unknown"
        
        # Create HTML content with D3.js visualization
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Age Group Representation</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 800px; height: 400px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
                .confidence-note { font-size: 14px; text-align: center; margin-top: 10px; color: #d62728; }
                .bar { fill: steelblue; }
                .bar:hover { fill: #5599ff; }
            </style>
        </head>
        <body>
            <div class="title">Age Group Representation in Dataset Images</div>
            <div class="chart-container">
                <svg id="bar-chart" width="800" height="400"></svg>
            </div>
            <div class="confidence-note">Estimation confidence: """ + confidence + """</div>
            <div class="footnote">Note: Age estimation is approximate and should be validated with human review</div>
            
            <script>
            // Data from Python analysis
            const ageData = """ + json.dumps(age_data) + """;
            
            // Process data for visualization
            const data = Object.entries(ageData)
                .map(([key, value]) => ({
                    category: key,
                    value: value
                }))
                .filter(d => d.value > 0); // Only show categories that appear
            
            // Define order for the categories
            const categoryOrder = ["child", "young_adult", "adult", "senior", "unidentified"];
            
            // Sort the data based on the predefined order
            data.sort((a, b) => categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category));
            
            // Map category names to display names
            const displayNames = {
                "child": "Child",
                "young_adult": "Young Adult",
                "adult": "Adult",
                "senior": "Senior", 
                "unidentified": "Unidentified"
            };
            
            // Update category names for display
            data.forEach(d => {
                d.displayName = displayNames[d.category] || d.category;
            });
            
            // Set up dimensions
            const margin = {top: 40, right: 20, bottom: 60, left: 40};
            const width = 800 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            // Create SVG
            const svg = d3.select("#bar-chart")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Create x scale
            const x = d3.scaleBand()
                .range([0, width])
                .domain(data.map(d => d.displayName))
                .padding(0.3);
            
            // Create y scale
            const y = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.value)])
                .nice()
                .range([height, 0]);
            
            // Add x axis
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x));
            
            // Add y axis
            svg.append("g")
                .call(d3.axisLeft(y).ticks(5).tickFormat(d => d3.format(".0%")(d)));
            
            // Create tooltip
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            // Add bars
            svg.selectAll(".bar")
                .data(data)
                .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("x", d => x(d.displayName))
                .attr("y", d => y(d.value))
                .attr("width", x.bandwidth())
                .attr("height", d => height - y(d.value))
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`${d.displayName}<br>${(d.value * 100).toFixed(1)}%`)
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
                .text("Age Group Distribution");
            
            // Add y axis label
            svg.append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", -margin.left + 10)
                .attr("x", -height / 2)
                .attr("dy", "1em")
                .style("text-anchor", "middle")
                .text("Proportion");
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_cultural_elements_visualization(self) -> str:
        """
        Generate visualization for cultural elements
        """
        filename = f"{self.output_dir}/cultural_elements.html"
        
        # Extract cultural elements data from aggregated results
        cultural_data = self.results.get("aggregated_results", {}).get("cultural_elements", {})
        
        # Filter out the estimation_confidence field
        if "estimation_confidence" in cultural_data:
            confidence = cultural_data["estimation_confidence"]
            cultural_data = {k: v for k, v in cultural_data.items() if k != "estimation_confidence"}
        else:
            confidence = "unknown"
        
        # Create HTML content with D3.js visualization (radar chart)
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Cultural Elements Representation</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 700px; height: 700px; margin: 0 auto; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
                .confidence-note { font-size: 14px; text-align: center; margin-top: 10px; color: #d62728; }
                .axis-name { font-size: 12px; }
                .radar-area { fill-opacity: 0.3; }
                .radar-stroke { stroke-width: 3px; fill: none; }
            </style>
        </head>
        <body>
            <div class="title">Cultural Elements in Dataset Images</div>
            <div class="chart-container">
                <svg id="radar-chart" width="700" height="700"></svg>
            </div>
            <div class="confidence-note">Estimation confidence: """ + confidence + """</div>
            <div class="footnote">Note: Cultural element detection is approximate and should be validated with human review</div>
            
            <script>
            // Data from Python analysis
            const culturalData = """ + json.dumps(cultural_data) + """;
            
            // Process data for visualization
            const data = Object.entries(culturalData)
                .filter(([key, _]) => key !== 'unidentified') // Exclude 'unidentified'
                .map(([key, value]) => ({
                    axis: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
                    value: value
                }));
            
            // Configuration
            const cfg = {
                radius: 5,
                w: 600,
                h: 600,
                factor: 1,
                factorLegend: .85,
                levels: 5,
                maxValue: Math.max(d3.max(data, d => d.value), 0.1),
                radians: 2 * Math.PI,
                color: d3.scaleOrdinal().range(["#6F257F"])
            };
            
            // Set up dimensions
            const width = cfg.w + 100;
            const height = cfg.h + 100;
            
            // Create SVG
            const svg = d3.select("#radar-chart")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", `translate(${width/2},${height/2})`);
            
            // Circular segments
            const levelFactor = cfg.factor * Math.min(cfg.w/2, cfg.h/2) / cfg.levels;
            
            // Create circular grid
            for (let level = 0; level < cfg.levels; level++) {
                const levelRadius = levelFactor * (level + 1);
                
                // Draw arcs for each level
                svg.append("circle")
                    .attr("cx", 0)
                    .attr("cy", 0)
                    .attr("r", levelRadius)
                    .style("fill", "none")
                    .style("stroke", "gray")
                    .style("stroke-opacity", "0.75")
                    .style("stroke-width", "0.3px");
                
                // Add labels for each level
                if (level === cfg.levels - 1) {
                    svg.append("text")
                        .attr("x", 5)
                        .attr("y", -levelRadius)
                        .attr("dy", "0.4em")
                        .style("font-size", "10px")
                        .style("fill", "#737373")
                        .text(d3.format(".0%")(cfg.maxValue));
                }
            }
            
            // Calculate total axis
            const total = data.length;
            const angleSlice = cfg.radians / total;
            
            // Create axes
            const axis = svg.selectAll(".axis")
                .data(data)
                .enter()
                .append("g")
                .attr("class", "axis");
            
            // Draw axis lines
            axis.append("line")
                .attr("x1", 0)
                .attr("y1", 0)
                .attr("x2", (d, i) => levelFactor * cfg.levels * Math.cos(angleSlice * i - Math.PI/2))
                .attr("y2", (d, i) => levelFactor * cfg.levels * Math.sin(angleSlice * i - Math.PI/2))
                .attr("class", "line")
                .style("stroke", "gray")
                .style("stroke-width", "1px");
            
            // Draw axis names
            axis.append("text")
                .attr("class", "axis-name")
                .attr("text-anchor", "middle")
                .attr("dy", "0.35em")
                .attr("x", (d, i) => levelFactor * (cfg.levels + 0.1) * Math.cos(angleSlice * i - Math.PI/2))
                .attr("y", (d, i) => levelFactor * (cfg.levels + 0.1) * Math.sin(angleSlice * i - Math.PI/2))
                .text(d => d.axis)
                .call(wrap, 60);
            
            // Draw radar chart blobs
            const radarLine = d3.lineRadial()
                .curve(d3.curveLinearClosed)
                .radius(d => (d.value / cfg.maxValue) * levelFactor * cfg.levels)
                .angle((d, i) => i * angleSlice);
            
            // Convert data for radial coordinates
            const radarData = [data.map((d, i) => ({
                angle: i,
                value: d.value
            }))];
            
            // Add radar blob
            svg.selectAll(".radar-area")
                .data(radarData)
                .enter()
                .append("path")
                .attr("class", "radar-area")
                .attr("d", radarLine)
                .style("fill", (d, i) => cfg.color(i))
                .style("fill-opacity", 0.5)
                .style("stroke-width", 2)
                .style("stroke", (d, i) => cfg.color(i))
                .style("filter", "url(#glow)");
            
            // Draw markers at data points
            svg.selectAll(".radar-circle")
                .data(data)
                .enter()
                .append("circle")
                .attr("class", "radar-circle")
                .attr("r", cfg.radius)
                .attr("cx", (d, i) => (d.value / cfg.maxValue) * levelFactor * cfg.levels * Math.cos(angleSlice * i - Math.PI/2))
                .attr("cy", (d, i) => (d.value / cfg.maxValue) * levelFactor * cfg.levels * Math.sin(angleSlice * i - Math.PI/2))
                .style("fill", "#fff")
                .style("stroke", cfg.color(0))
                .style("stroke-width", 2);
            
            // Add tooltips
            const tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("background", "#f9f9f9")
                .style("border", "1px solid #ccc")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("opacity", 0);
            
            svg.selectAll(".tooltip-area")
                .data(data)
                .enter()
                .append("circle")
                .attr("class", "tooltip-area")
                .attr("r", cfg.radius * 4) // Larger invisible circle for better tooltip triggering
                .attr("cx", (d, i) => (d.value / cfg.maxValue) * levelFactor * cfg.levels * Math.cos(angleSlice * i - Math.PI/2))
                .attr("cy", (d, i) => (d.value / cfg.maxValue) * levelFactor * cfg.levels * Math.sin(angleSlice * i - Math.PI/2))
                .style("fill", "none")
                .style("pointer-events", "all")
                .on("mouseover", function(event, d) {
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`${d.axis}<br>${(d.value * 100).toFixed(1)}%`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition().duration(500).style("opacity", 0);
                });
            
            // Wrapping function for axis labels
            function wrap(text, width) {
                text.each(function() {
                    var text = d3.select(this),
                        words = text.text().split(/\\s+/).reverse(),
                        word,
                        line = [],
                        lineNumber = 0,
                        lineHeight = 1.4, // ems
                        y = text.attr("y"),
                        x = text.attr("x"),
                        dy = parseFloat(text.attr("dy")),
                        tspan = text.text(null).append("tspan").attr("x", x).attr("y", y).attr("dy", dy + "em");
                    
                    while (word = words.pop()) {
                        line.push(word);
                        tspan.text(line.join(" "));
                        if (tspan.node().getComputedTextLength() > width) {
                            line.pop();
                            tspan.text(line.join(" "));
                            line = [word];
                            tspan = text.append("tspan").attr("x", x).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
                        }
                    }
                });
            }
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_bias_index_visualization(self) -> str:
        """
        Generate visualization for overall bias index
        """
        filename = f"{self.output_dir}/bias_index.html"
        
        # Extract aggregated results
        aggregated_results = self.results.get("aggregated_results", {})
        
        # Calculate bias indices (simplified for demonstration)
        # In a real implementation, you would use more sophisticated methods
        
        # Skin tone diversity score (higher is better)
        skin_tone_data = aggregated_results.get("skin_tone_distribution", {})
        skin_tone_values = [v for k, v in skin_tone_data.items() if k != "estimation_confidence"]
        skin_tone_diversity = 0
        if skin_tone_values:
            # Calculate entropy as diversity measure
            total = sum(skin_tone_values)
            if total > 0:
                probabilities = [v / total for v in skin_tone_values if v > 0]
                # Shannon entropy calculation
                skin_tone_diversity = -sum(p * np.log2(p) for p in probabilities) / np.log2(len(probabilities)) if probabilities else 0
        
        # Gender balance score (higher is better)
        gender_data = aggregated_results.get("gender_representation", {})
        gender_values = [v for k, v in gender_data.items() if k != "estimation_confidence"]
        gender_balance = 0
        if gender_values:
            # Calculate entropy as diversity measure
            total = sum(gender_values)
            if total > 0:
                probabilities = [v / total for v in gender_values if v > 0]
                # Shannon entropy calculation
                gender_balance = -sum(p * np.log2(p) for p in probabilities) / np.log2(len(probabilities)) if probabilities else 0
        
        # Age diversity score (higher is better)
        age_data = aggregated_results.get("age_representation", {})
        age_values = [v for k, v in age_data.items() if k != "estimation_confidence"]
        age_diversity = 0
        if age_values:
            # Calculate entropy as diversity measure
            total = sum(age_values)
            if total > 0:
                probabilities = [v / total for v in age_values if v > 0]
                # Shannon entropy calculation
                age_diversity = -sum(p * np.log2(p) for p in probabilities) / np.log2(len(probabilities)) if probabilities else 0
        
        # Cultural diversity score (higher is better)
        cultural_data = aggregated_results.get("cultural_elements", {})
        cultural_values = [v for k, v in cultural_data.items() if k not in ["estimation_confidence", "unidentified"]]
        cultural_diversity = 0
        if cultural_values:
            # Calculate entropy as diversity measure
            total = sum(cultural_values)
            if total > 0:
                probabilities = [v / total for v in cultural_values if v > 0]
                # Shannon entropy calculation
                cultural_diversity = -sum(p * np.log2(p) for p in probabilities) / np.log2(len(probabilities)) if probabilities else 0
        
        # Create bias indices for visualization
        bias_indices = {
            "Skin Tone Diversity": skin_tone_diversity,
            "Gender Balance": gender_balance,
            "Age Diversity": age_diversity,
            "Cultural Diversity": cultural_diversity
        }
        
        # Calculate overall bias index (average of all indices)
        overall_bias_index = sum(bias_indices.values()) / len(bias_indices) if bias_indices else 0
        
        # Create HTML content with D3.js visualization (gauge charts)
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Bias Index Visualization</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { width: 800px; margin: 0 auto; }
                .gauge-container { display: inline-block; width: 50%; text-align: center; margin-bottom: 30px; }
                .title { font-size: 18px; text-align: center; margin-bottom: 20px; }
                .subtitle { font-size: 16px; text-align: center; margin-bottom: 10px; }
                .footnote { font-size: 12px; text-align: center; margin-top: 20px; color: #777; }
                .overall-score { font-size: 24px; text-align: center; margin: 20px 0; }
                .overall-label { font-size: 16px; text-align: center; margin-bottom: 10px; }
                .interpretation-guide { margin-top: 30px; text-align: left; }
                .interpretation-guide h3 { font-size: 16px; }
                .interpretation-guide ul { padding-left: 20px; }
            </style>
        </head>
        <body>
            <div class="title">Image Dataset Bias Index</div>
            <div class="overall-score" id="overall-score">Overall Diversity Score: <span id="score-value"></span></div>
            <div class="subtitle">Diversity Metrics</div>
            
            <div class="chart-container" id="gauge-container">
                <!-- Gauges will be placed here -->
            </div>
            
            <div class="interpretation-guide">
                <h3>Interpretation Guide:</h3>
                <ul>
                    <li><strong>Skin Tone Diversity:</strong> Measures the diversity of skin tones in the dataset</li>
                    <li><strong>Gender Balance:</strong> Measures how balanced gender representation is in the dataset</li>
                    <li><strong>Age Diversity:</strong> Measures the diversity of age groups in the dataset</li>
                    <li><strong>Cultural Diversity:</strong> Measures the diversity of cultural elements in the dataset</li>
                </ul>
                <p>All scores range from 0 (very low diversity) to 1 (high diversity). Higher scores indicate a more balanced and diverse dataset.</p>
            </div>
            
            <div class="footnote">Note: These diversity scores are computed using statistical measures of diversity (entropy) and should be used as general indicators rather than absolute measures.</div>
            
            <script>
            // Data from Python analysis
            const biasIndices = """ + json.dumps(bias_indices) + """;
            const overallBiasIndex = """ + str(overall_bias_index) + """;
            
            // Set the overall score
            d3.select("#score-value")
                .text(`${(overallBiasIndex * 100).toFixed(1)}%`)
                .style("color", overallBiasIndex > 0.7 ? "#2c7bb6" : overallBiasIndex > 0.5 ? "#fdae61" : "#d7191c");
            
            // Function to create a gauge chart
            function createGauge(containerId, name, value) {
                // Configuration
                const config = {
                    size: 200,
                    clipWidth: 200,
                    clipHeight: 110,
                    ringInset: 20,
                    ringWidth: 20,
                    
                    pointerWidth: 10,
                    pointerTailLength: 5,
                    pointerHeadLengthPercent: 0.9,
                    
                    minValue: 0,
                    maxValue: 1,
                    
                    minAngle: -90,
                    maxAngle: 90,
                    
                    transitionMs: 750,
                    
                    // Colors for the gauge
                    majorTicks: 5,
                    labelFormat: d3.format('.1f'),
                    labelInset: 10,
                    
                    arcColorFn: d3.scaleLinear()
                        .domain([0, 0.5, 1])
                        .range(["#d7191c", "#fdae61", "#1a9641"])
                };
                
                const range = config.maxAngle - config.minAngle;
                const r = config.size / 2;
                
                // Create container for this gauge
                const container = d3.select("#gauge-container")
                    .append("div")
                    .attr("class", "gauge-container")
                    .attr("id", containerId);
                
                container.append("div")
                    .attr("class", "gauge-label")
                    .style("font-weight", "bold")
                    .style("margin-bottom", "5px")
                    .text(name);
                
                // Create SVG for the gauge
                const svg = container
                    .append("svg")
                    .attr("width", config.clipWidth)
                    .attr("height", config.clipHeight);
                
                const centerTx = `translate(${r},${r})`;
                
                // Create arc for the gauge
                const arc = d3.arc()
                    .innerRadius(r - config.ringWidth - config.ringInset)
                    .outerRadius(r - config.ringInset)
                    .startAngle((d) => {
                        const ratio = d * range / (config.maxValue - config.minValue);
                        return deg2rad(config.minAngle + ratio);
                    })
                    .endAngle((d) => {
                        const ratio = (d + 0.1) * range / (config.maxValue - config.minValue);
                        return deg2rad(config.minAngle + ratio);
                    });
                
                // Create group for arcs
                const arcs = svg.append("g")
                    .attr("class", "arc")
                    .attr("transform", centerTx);
                
                // Add arc segments
                const segments = [...Array(10).keys()].map(i => i / 10);
                arcs.selectAll("path")
                    .data(segments)
                    .enter()
                    .append("path")
                    .attr("fill", d => config.arcColorFn(d))
                    .attr("d", arc);
                
                // Create group for the gauge
                const gauge = svg.append("g")
                    .attr("class", "gauge")
                    .attr("transform", centerTx);
                
                // Add labels
                const lg = gauge.append("g")
                    .attr("class", "label");
                
                lg.selectAll("text")
                    .data([0, 0.5, 1])
                    .enter()
                    .append("text")
                    .attr("transform", d => {
                        const ratio = d * range / (config.maxValue - config.minValue);
                        const angle = config.minAngle + ratio;
                        return `rotate(${angle}) translate(0,${-r + config.labelInset})`;
                    })
                    .style("text-anchor", d => d === 0 ? "start" : d === 1 ? "end" : "middle")
                    .text(d => config.labelFormat(d));
                
                // Create needle
                const lineData = [
                    [config.pointerWidth / 2, 0],
                    [0, -config.pointerHeadLengthPercent * r],
                    [-(config.pointerWidth / 2), 0],
                    [0, config.pointerTailLength],
                    [config.pointerWidth / 2, 0]
                ];
                
                const pointerLine = d3.line().curve(d3.curveLinear);
                
                const pg = gauge.append("g")
                    .data([lineData])
                    .attr("class", "pointer");
                
                // Add pointer
                const pointer = pg.append("path")
                    .attr("d", pointerLine)
                    .attr("transform", `rotate(${config.minAngle})`);
                
                // Update pointer position
                function updateGauge(value) {
                    const ratio = scale(value);
                    const angle = config.minAngle + (ratio * range);
                    
                    // Set pointer position
                    pointer.transition()
                        .duration(config.transitionMs)
                        .ease(d3.easeElastic)
                        .attr("transform", `rotate(${angle})`);
                    
                    // Add value text
                    container.select(".gauge-value").remove();
                    container.append("div")
                        .attr("class", "gauge-value")
                        .style("font-size", "16px")
                        .style("font-weight", "bold")
                        .style("margin-top", "5px")
                        .style("color", config.arcColorFn(value))
                        .text(`${(value * 100).toFixed(1)}%`);
                }
                
                // Helper functions
                function scale(value) {
                    return (value - config.minValue) / (config.maxValue - config.minValue);
                }
                
                function deg2rad(deg) {
                    return deg * Math.PI / 180;
                }
                
                // Initialize gauge with value
                updateGauge(value);
            }
            
            // Create a gauge for each bias index
            Object.entries(biasIndices).forEach(([name, value], i) => {
                createGauge(`gauge-${i}`, name, value);
            });
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename


def generate_image_analysis_report(
    analysis_results: Dict[str, Any], 
    visualization_paths: Dict[str, str], 
    output_path: str = "image_analysis_report.html"
):
    """
    Generate an HTML report for image analysis results
    
    Parameters:
    -----------
    analysis_results : Dict[str, Any]
        Results from image analysis
    
    visualization_paths : Dict[str, str]
        Paths to visualization files
    
    output_path : str
        Path to save the report
        
    Returns:
    --------
    str
        Path to the generated report
    """
    # Get key results
    aggregated_results = analysis_results.get("aggregated_results", {})
    sample_size = aggregated_results.get("sample_size", 0)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>EthiViz Image Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ text-align: center; margin-bottom: 30px; }}
            h2 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top: 30px; }}
            .timestamp {{ text-align: center; margin-bottom: 30px; color: #777; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
            .summary-item {{ margin-bottom: 10px; }}
            .summary-label {{ font-weight: bold; }}
            .visualization-container {{ margin: 30px 0; }}
            .visualization-iframe {{ width: 100%; height: 600px; border: none; }}
            .notes {{ font-style: italic; color: #666; margin-top: 5px; }}
            .footer {{ text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #777; }}
            .caution-note {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>EthiViz Image Analysis Report</h1>
            <div class="timestamp">Generated on {timestamp}</div>
            
            <div class="summary">
                <h2>Analysis Summary</h2>
                <div class="summary-item">
                    <span class="summary-label">Sample Size:</span> {sample_size} images
                </div>
                <div class="summary-item">
                    <span class="summary-label">Analysis Method:</span> Lightweight image analysis using color and texture features
                </div>
                <div class="caution-note">
                    <strong>Note:</strong> This analysis uses lightweight approximation methods that prioritize computational efficiency over perfect accuracy. 
                    Results should be considered as indicators rather than definitive measurements, especially for demographic attributes.
                    Human validation is recommended for critical applications.
                </div>
            </div>
            
            <h2>Bias Index</h2>
            <p>
                The overall bias index provides a combined measure of diversity across multiple dimensions. 
                Higher scores indicate greater diversity and balance in representation.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('bias_index', '')}"></iframe>
            </div>
            
            <h2>Skin Tone Distribution</h2>
            <p>
                This visualization shows the distribution of skin tones across the dataset based on the Fitzpatrick scale.
                A balanced distribution across multiple skin types indicates greater diversity.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('skin_tone_distribution', '')}"></iframe>
            </div>
            <div class="notes">
                Note: Skin tone analysis is based on pixel color sampling and provides an approximation rather than precise measurement.
            </div>
            
            <h2>Gender Representation</h2>
            <p>
                This visualization shows the estimated gender distribution in the dataset.
                Equal representation across genders indicates a more balanced dataset.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('gender_representation', '')}"></iframe>
            </div>
            <div class="notes">
                Note: Gender estimation is highly approximated without advanced AI models and should be treated as low confidence.
            </div>
            
            <h2>Age Group Representation</h2>
            <p>
                This visualization shows the estimated age group distribution in the dataset.
                Representation across multiple age groups indicates greater diversity.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('age_representation', '')}"></iframe>
            </div>
            <div class="notes">
                Note: Age estimation is highly approximated without advanced AI models and should be treated as low confidence.
            </div>
            
            <h2>Cultural Elements</h2>
            <p>
                This visualization shows the estimated distribution of cultural elements in the dataset.
                A more diverse representation of cultural elements indicates greater cultural inclusion.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('cultural_elements', '')}"></iframe>
            </div>
            <div class="notes">
                Note: Cultural element detection is highly approximated without advanced AI models and should be treated as low confidence.
            </div>
            
            <h2>Color Distribution</h2>
            <p>
                This visualization shows the color distribution across the dataset.
                Color patterns can sometimes indicate unintentional biases in visual representation.
            </p>
            <div class="visualization-container">
                <iframe class="visualization-iframe" src="{visualization_paths.get('color_distribution', '')}"></iframe>
            </div>
            
            <h2>Recommendations</h2>
            <ul>
                <li>Consider validating the results with human reviewers, especially for demographic attributes</li>
                <li>If imbalances are detected, consider diversifying your image dataset to improve representation</li>
                <li>For critical applications, consider using more advanced AI models for demographic analysis</li>
                <li>Review images with cultural elements to ensure appropriate and respectful representation</li>
            </ul>
            
            <div class="footer">
                <p>EthiViz - Cultural Bias Analysis Platform</p>
                <p>Copyright &copy; {datetime.now().year} All Rights Reserved</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save HTML report
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    return output_path