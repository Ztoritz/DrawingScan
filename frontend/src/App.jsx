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

  // Check server health on mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const res = await axios.get(`${apiUrl}/`);
        setServerStatus('online');
        if (res.data.engine) {
          // Explicitly showing the user what model is running
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

  return (
    <div className="min-h-screen p-8 lg:p-12 relative">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-12 text-center animate-fade-in relative">

          {/* Server Status Indicator */}
          <div className="absolute top-0 right-0 flex flex-col items-end space-y-2">
            <div className="flex items-center space-x-2 bg-white/5 px-3 py-1 rounded-full border border-white/10">
              <div className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : serverStatus === 'offline' ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'}`}></div>
              <span className="text-xs text-gray-400 font-mono tracking-wider uppercase">
                {serverStatus === 'online' ? 'System Online' : serverStatus === 'offline' ? 'Backend Disconnected' : 'Syncing...'}
              </span>
            </div>

            {/* Engine Badge - NOW LARGER AND EXPLICIT */}
            <div className={`mt-2 inline-flex items-center space-x-2 px-4 py-2 rounded-full border text-sm font-bold tracking-wide uppercase shadow-lg
                  ${activeEngine.includes('Gemini')
                ? 'bg-gradient-to-r from-purple-600 to-blue-600 border-purple-400 text-white'
                : 'bg-gray-800 border-gray-600 text-gray-300'}`}>
              <span className="text-lg">
                {activeEngine.includes('Gemini') ? '⚡' : '�'}
              </span>
              <span>
                {/* If Gemini, explicitly say Flash if backend sends it, or just Gemini */}
                {activeEngine || 'Unknown Engine'}
              </span>
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
            <span className="text-purple-400 font-bold mx-1">Gemini Flash AI</span>
            (or local OCR fallback).
          </p>
        </header>

        {/* Main Content Area */}
        <div className="space-y-12">
          {/* Upload Area */}
          <div className={`transition-all duration-500 ${results ? 'scale-90 opacity-80 hover:scale-100 hover:opacity-100' : ''}`}>
            <div className={serverStatus === 'offline' ? 'pointer-events-none opacity-50 grayscale' : ''}>
              <UploadZone onFileSelected={handleFileSelected} />
            </div>
            {serverStatus === 'offline' && (
              <p className="text-red-400 text-center mt-4 text-sm">Cannot upload: Backend server is unreachable.</p>
            )}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
              <div className="relative w-24 h-24 mb-6">
                {/* Flash Icon Animation */}
                <div className="absolute inset-0 flex items-center justify-center text-4xl animate-pulse">
                  ⚡
                </div>
                <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                <div className="absolute inset-0 rounded-full border-t-4 border-yellow-400 animate-spin"></div>
              </div>
              <p className="text-xl font-medium text-white animate-pulse">Processing with Gemini Flash...</p>
              <p className="text-sm text-gray-500 mt-2">Extracting GD&T and Dimensions</p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-center text-red-200 animate-fade-in font-mono text-sm break-all">
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
