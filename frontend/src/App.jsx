import React, { useState } from 'react';
import UploadZone from './components/UploadZone';
import ResultsList from './components/ResultsList';
import axios from 'axios';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelected = async (file) => {
    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Use environment variable for API URL (set in Coolify/Docker)
      // Fallback to localhost for local development if not set
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await axios.post(`${apiUrl}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.results);
    } catch (err) {
      console.error(err);
      setError('Failed to process file. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <header className="mb-12 text-center animate-fade-in">
          <h1 className="text-5xl font-black tracking-tight mb-4">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-secondary to-accent">
              Scan-Drawing
            </span>
            <span className="text-white ml-2">App</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Extract dimensions, tolerances, and GD&T symbols from technical drawings instantously using AI and Optical Character Recognition.
          </p>
        </header>

        {/* Main Content Area */}
        <div className="space-y-12">

          {/* Upload Area */}
          <div className={`transition-all duration-500 ${results ? 'scale-90 opacity-80 hover:scale-100 hover:opacity-100' : ''}`}>
            <UploadZone onFileSelected={handleFileSelected} />
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
              <div className="relative w-20 h-20 mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                <div className="absolute inset-0 rounded-full border-t-4 border-primary animate-spin"></div>
              </div>
              <p className="text-xl font-medium text-white animate-pulse">Scanning Drawing...</p>
              <p className="text-sm text-gray-500 mt-2">Running OCR and Pattern Matching</p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-center text-red-200 animate-fade-in">
              {error}
            </div>
          )}

          {/* Results */}
          {results && <ResultsList data={results} />}

        </div>
      </div>
    </div>
  );
}

export default App;
