# Photoshop Web

A professional web-based image editing application featuring a dynamic layer management system. The project is built using a high-performance FastAPI (Python) backend and an interactive frontend powered by the Fabric.js (HTML5 Canvas) library.

## Architecture & Features

*   **Monolithic Structure:** The entire user interface (HTML, CSS, JS) is embedded directly into the backend server. This completely eliminates browser caching issues with static assets and simplifies deployment.
*   **Dynamic Layer Management:** Full control over canvas objects (images, text, shapes) via the right-hand sidebar. Supports visibility toggling, transformation locking, and z-index reordering (moving layers up/down).
*   **Default Canvas Background:** The project automatically initializes with an interactive, selectable white background rectangle acting as the base layer.
*   **Asynchronous Filter Processing:** Image filters (Grayscale, Blur, Inversion) are processed on the server side using the Pillow (PIL) library via API endpoints.

---

## Environment Requirements

To run this application, you need **Python 3.9 or higher** installed on your system.

### Required Libraries

The following dependencies must be installed in your Python environment for the application to function correctly:

*   `fastapi` — The core web framework used to build the backend API endpoints and serve the application.
*   `uvicorn` — An ASGI web server implementation used to run and host the FastAPI application locally.
*   `pillow` — An advanced image processing library used for manipulating pixels and applying filters on the server side.
*   `python-multipart` — **CRITICAL:** Required by FastAPI to correctly parse, stream, and process uploaded image files via HTTP POST multipart forms.

---

## Installation & Setup Guide

### 1. Project Directory Preparation
Ensure that your `main.py` file is located in the root directory of your project folder.

### 2. Install Dependencies
Open your terminal inside the project folder and execute the following command to install all required libraries at once:

```bash
pip install fastapi uvicorn pillow python-multipart
