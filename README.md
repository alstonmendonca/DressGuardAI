# DressGuard AI

A computer-vision-powered clothing compliance detection system built
with YOLOv8 for real-time dress-code validation.

------------------------------------------------------------------------

## Table of Contents

-   Overview
-   Features
-   Architecture
-   Prerequisites
-   Installation
-   Running the Application
-   API Endpoints
-   Configuration
-   Network Access
-   Detection Flow
-   Troubleshooting
-   Development
-   Performance Optimization
-   Security Considerations
-   Additional Resources
-   License
-   Contributors
-   Contributing

------------------------------------------------------------------------

## Overview

DressGuard is a full-stack system designed to detect clothing items and
validate them against predefined compliance rules.

It consists of:

-   FastAPI backend
-   React (Vite) frontend
-   YOLOv8-based object detection engine

Supports real-time detection via:

-   Webcam
-   Image upload
-   Video file
-   IP cameras

------------------------------------------------------------------------

## Features

-   Multiple Detection Modes (Image, Webcam, Video, IP Camera)
-   Multi-Model Support (Switch between YOLO models dynamically)
-   Compliance Checking (Configurable validation rules)
-   Distance Checking (Ensures correct user positioning)
-   Real-Time Visualization (Bounding boxes and confidence scores)
-   Structured Rotating Logs
-   RESTful API with OpenAPI documentation
-   Modern Responsive UI (React + Vite)
-   Performance-Optimized Frame Handling

------------------------------------------------------------------------

## Architecture

    DressGuard/
    ├── backend/ (FastAPI + YOLOv8)
    │   ├── main.py
    │   ├── detector.py
    │   ├── config.py
    │   └── utils/
    │       ├── compliance.py
    │       └── logger.py
    │
    └── frontend/ (React + Vite)
        ├── src/
        │   ├── components/
        │   └── utils/
        └── public/

------------------------------------------------------------------------

## Prerequisites

### Backend

-   Python 3.8+
-   pip
-   CUDA 12.x (optional, for GPU acceleration)

### Frontend

-   Node.js 16+
-   Modern browser

------------------------------------------------------------------------

## Installation

### 1. Clone Repository

    git clone <repository-url>
    cd DressGuard

### 2. Backend Setup

    pip install -r requirements.txt
    mkdir models
    cp .env.example .env

Add your YOLO model files inside the `models/` directory.

### 3. Frontend Setup

    cd frontend
    npm install
    cp .env.example .env
    cd ..

------------------------------------------------------------------------

## Running the Application

### Start Backend

    uvicorn main:app --reload

For network access:

    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Backend URLs:

-   http://localhost:8000
-   http://localhost:8000/docs

### Start Frontend

    cd frontend
    npm run dev

------------------------------------------------------------------------

## API Endpoints

  Method   Endpoint           Description
  -------- ------------------ ----------------------------
  GET      `/`                API information
  GET      `/health`          Health check
  GET      `/models`          List available YOLO models
  GET      `/current-model`   Get active model
  POST     `/detect`          Detect clothing in image
  POST     `/switch-model`    Switch YOLO model

------------------------------------------------------------------------

## Configuration

### Compliance Rules (config.py)

    COMPLIANT_CLOTHES = {"full sleeve shirt", "pants", "id card"}
    NON_COMPLIANT_CLOTHES = {"t-shirt", "shorts"}

    COMPLIANCE_RULES = {
        "min_confidence": 0.5,
        "require_all_compliant": True
    }

------------------------------------------------------------------------

## Troubleshooting

### Model File Missing

Ensure `.pt` files are located in the `models/` directory.

### CUDA Out of Memory

Disable GPU in `config.py`:

    ENABLE_GPU = False

------------------------------------------------------------------------

## Security Considerations

-   Validate upload file types
-   Use environment variables for sensitive information
-   Employ HTTPS in production
-   Restrict CORS origins
-   Consider implementing rate limiting

------------------------------------------------------------------------

## License

MIT License

------------------------------------------------------------------------

## Contributors

Alston Daniel Mendonca
Reevan D Mello

------------------------------------------------------------------------

## Contributing

1.  Fork the repository
2.  Create a new branch
3.  Commit your changes
4.  Open a Pull Request
