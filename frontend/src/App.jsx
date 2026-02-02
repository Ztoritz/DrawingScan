import React, { useState, useEffect } from 'react';
import UploadZone from './components/UploadZone';
import ResultsList from './components/ResultsList';
import axios from 'axios';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // checking, online, offline
  const [activeEngine, setActiveEngine] = useState('Checking...');

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const [previewUrl, setPreviewUrl] = useState(null);
  const [highlightBox, setHighlightBox] = useState(null);

  // Listen for Smart Overlay events from ResultsList
  useEffect(() => {
    const handleHighlight = (e) => setHighlightBox(e.detail);
    window.addEventListener('highlight-box', handleHighlight);
    return () => window.removeEventListener('highlight-box', handleHighlight);
  }, []);

  // Check server health on mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const res = await axios.get(`${apiUrl}/`);
        setServerStatus('online');
        if (res.data.engine) {
          setActiveEngine(res.data.engine);
        }
      } catch (err) {
        console.error("Server Health Check Failed:", err);
        setServerStatus('offline');
        setActiveEngine('Unknown');
      }
    };
    checkServer();
    const interval = setInterval(checkServer, 10000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const handleFileSelected = async (file) => {
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${apiUrl}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.results);
    } catch (err) {
      console.error(err);
      const backendMsg = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError(`Failed to process: ${backendMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const clearFile = () => {
    setPreviewUrl(null);
    setResults(null);
    setHighlightBox(null);
  }

  return (
    <div className="min-h-screen p-8 lg:p-12 relative overflow-x-hidden">
      <div className="max-w-6xl mx-auto z-10 relative">
        {/* Header */}
        <header className="mb-8 text-center animate-fade-in relative">

          <div className="absolute top-0 right-0 flex flex-col items-end space-y-2">
            <div className="flex items-center space-x-2 bg-white/5 px-3 py-1 rounded-full border border-white/10">
              <div className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : serverStatus === 'offline' ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'}`}></div>
              <span className="text-xs text-gray-400 font-mono tracking-wider uppercase">
                {serverStatus === 'online' ? 'System Online' : serverStatus === 'offline' ? 'Backend Disconnected' : 'Syncing...'}
              </span>
            </div>

            <div className={`mt-2 inline-flex items-center space-x-2 px-4 py-2 rounded-full border text-sm font-bold tracking-wide uppercase shadow-lg
                  ${activeEngine.includes('Qwen')
                ? 'bg-gradient-to-r from-emerald-600 to-teal-600 border-emerald-400 text-white'
                : activeEngine.includes('Gemini')
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 border-purple-400 text-white'
                  : 'bg-gray-800 border-gray-600 text-gray-300'}`}>
              <span className="text-lg">
                {activeEngine.includes('Qwen') ? '🧠' : activeEngine.includes('Gemini') ? '⚡' : ''}
              </span>
              <span>{activeEngine}</span>
            </div>
          </div>

          <h1 className="text-5xl font-black tracking-tight mb-4 mt-8">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-secondary to-accent">
              Scan-Drawing
            </span>
            <span className="text-white ml-2">App</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Extract dimensions, tolerances, and GD&T symbols from technical drawings using
            <span className="text-emerald-400 font-bold mx-1">Qwen 2.5 Vision</span>
            (or local OCR fallback).
          </p>
        </header>

        {/* Main Content Area */}
        <div className="space-y-8">

          {/* 1. Upload Zone (Hidden if preview exists to save space, or minimized) */}
          {!previewUrl && (
            <div className="animate-fade-in">
              <div className={serverStatus === 'offline' ? 'pointer-events-none opacity-50 grayscale' : ''}>
                <UploadZone onFileSelected={handleFileSelected} />
              </div>
              {serverStatus === 'offline' && <p className="text-red-400 text-center mt-4">Backend disconnected</p>}
            </div>
          )}

          {/* 2. PREVIEW AREA + LASER SCAN + SMART OVERLAY */}
          {previewUrl && (
            <div className="relative animate-fade-in flex justify-center mb-8">
              <div className="relative inline-block group rounded-lg overflow-hidden border border-white/10 shadow-2xl">

                {/* Close/Clear Button */}
                {!loading && (
                  <button
                    onClick={clearFile}
                    className="absolute top-2 right-2 z-30 bg-black/50 hover:bg-red-500 text-white p-2 rounded-full backdrop-blur-md transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                )}

                {/* Main Image */}
                <img
                  src={previewUrl}
                  alt="Preview"
                  className={`block max-h-[600px] w-auto transition-opacity duration-1000 ${loading ? 'opacity-50' : 'opacity-100'}`}
                />

                {/* LASER SCANNING EFFECT (Only when loading) */}
                {loading && (
                  <div className="absolute inset-0 z-20 pointer-events-none">
                    {/* The Moving Line */}
                    <div className="absolute w-full h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-scan shadow-[0_0_20px_#34d399]"></div>

                    {/* Grid Overlay */}
                    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
                    <div className="absolute inset-0 border-2 border-emerald-500/30 rounded-lg"></div>

                    {/* Status Check Text */}
                    <div className="absolute bottom-4 left-0 right-0 text-center">
                      <span className="inline-block bg-black/70 backdrop-blur px-3 py-1 rounded text-emerald-400 font-mono text-sm animate-pulse border border-emerald-500/30">
                        ACTIVATING VISION MATRIX...
                      </span>
                    </div>
                  </div>
                )}

                {/* SMART OVERLAY (Only when NOT loading) */}
                {!loading && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox="0 0 1000 1000"
                    preserveAspectRatio="none"
                  >
                    {highlightBox && (
                      <rect
                        x={highlightBox[1]} // xmin
                        y={highlightBox[0]} // ymin
                        width={highlightBox[3] - highlightBox[1]} // Width
                        height={highlightBox[2] - highlightBox[0]} // Height
                        fill="rgba(239, 68, 68, 0.15)"
                        stroke="#ef4444"
                        strokeWidth="3"
                        vectorEffect="non-scaling-stroke"
                        className="animate-pulse"
                      />
                    )}
                  </svg>
                )}
              </div>
            </div>
          )}

          {/* 3. Results Table */}
          {results && <ResultsList data={results} />}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-center text-red-200 animate-fade-in">
              {error}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
