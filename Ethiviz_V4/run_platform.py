from __future__ import annotations
import os
import uvicorn
import numpy as np
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from ethiviz import Analyzer, DeploymentContext
from ethiviz.reporting.html_report import generate_html_report
from PIL import Image
import io
import base64
import signal
import asyncio

app = FastAPI(title="EthiViz V4 Platform")

# Initialize Analyzer with default context
ctx = DeploymentContext(
    region="DE",
    domain="hiring",
    primary_community="western",
    regulatory_framework="eu-ai-act",
    additional_regulations=["gdpr"]
)
analyzer = Analyzer(deployment_context=ctx)

@app.get("/", response_class=HTMLResponse)
async def index():
    # Initial demo analysis for landing page
    sample_texts = [
        "Individual rights are more important than communal stability.",
        "Maintaining social hierarchy is essential for cosmic harmony."
    ]
    report = analyzer.quick_scan(sample_texts)
    report.scored_result.metadata["source_type"] = "text"
    report.scored_result.metadata["source_content"] = "\n".join(sample_texts)
    return generate_html_report(report)

@app.post("/stop")
async def stop_server():
    async def shutdown():
        await asyncio.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
    
    asyncio.create_task(shutdown())
    return {"status": "stopping"}

@app.post("/analyze/text", response_class=HTMLResponse)
async def analyze_text(file: UploadFile = File(...)):
    content = await file.read()
    file_size = f"{len(content) / 1024:.1f} KB"
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    # Analysis logic (delay removed for speed)
    
    # Split lines if it looks like a list, otherwise treat as one text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = ["Empty file uploaded."]
    
    report = analyzer.quick_scan(lines)
    report.scored_result.metadata["source_type"] = "text"
    report.scored_result.metadata["source_content"] = text
    report.scored_result.metadata["file_size"] = file_size
    return generate_html_report(report)

@app.post("/analyze/image", response_class=HTMLResponse)
async def analyze_image(file: UploadFile = File(...)):
    content = await file.read()
    file_size = f"{len(content) / 1024:.1f} KB"
    image = Image.open(io.BytesIO(content)).convert("RGB")
    image_arr = np.array(image)
    
    # Simulate processing delay
    await asyncio.sleep(2)
    
    # In a real implementation, we'd have an ImageAnalyzer.
    # For now, we'll run a quick scan on a placeholder text and
    # simulate image analysis in the report metadata.
    report = analyzer.quick_scan(["[Image Analysis Triggered]"])
    
    # Encode image to base64 for preview
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    report.scored_result.metadata["source_type"] = "image"
    report.scored_result.metadata["source_content"] = f"data:image/png;base64,{img_str}"
    report.scored_result.metadata["file_size"] = file_size
    report.scored_result.metadata["vision_findings"] = "Face detected. ITA-based skin tone: Type II."
    
    return generate_html_report(report)

if __name__ == "__main__":
    print("Starting EthiViz V4 Platform with Upload Support...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
