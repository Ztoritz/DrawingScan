# Scan-Drawing App

A full-stack application to extract dimensions and tolerance data from engineering drawings (PDF).

## Prerequisites (Critical)

Since this app uses OCR and PDF conversion, you need to install these tools on your Windows machine:

1.  **Tesseract OCR**
    *   Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
    *   **IMPORTANT**: During installation, add Tesseract to your **PATH**.
    
2.  **Poppler** (for PDF to Image conversion)
    *   Download the latest binary release [here](https://github.com/oschwartz10612/poppler-windows/releases/).
    *   Extract the zip.
    *   Add the `bin` folder (e.g., `C:\Program Files\poppler-xx\bin`) to your System **PATH** environment variable.

## Setup & Running

### Backend
1.  Navigate to `backend`:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the server:
    ```bash
    python main.py
    ```
    Server runs at `http://localhost:8000`.

### Frontend
1.  Navigate to `frontend`:
    ```bash
    cd frontend
    ```
2.  Install dependencies (if not already done):
    ```bash
    npm install
    npm install axios
    ```
3.  Run the dev server:
    ```bash
    npm run dev
    ```
    App runs at `http://localhost:5173`.

## Usage
1.  Open the web app.
2.  Drag and drop a PDF drawing.
3.  View the extracted dimensions and symbols.
