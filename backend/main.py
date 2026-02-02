from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import extractor
import tempfile

app = FastAPI()

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Initialize the OCR model on startup to avoid timeout on first request
    extractor.init_reader()

@app.get("/")
def read_root():
    return {
        "message": "Scan-Drawing API is running",
        "engine": extractor.get_active_engine()
    }

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF or Image (JPEG/PNG/TIFF/WEBP).")

    # Save uploaded file typically
    try:
        suffix = ".pdf" if file.content_type == "application/pdf" else os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        
        # Process the file
        results = extractor.process_file(tmp_file_path)
        
        # Cleanup
        os.remove(tmp_file_path)
        
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
