import React, { useState } from 'react';
import UploadZone from './components/UploadZone';
import ResultsList from './components/ResultsList';
import axios from 'axios';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // checking, online, offline

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Check server health on mount
  React.useEffect(() => {
    const checkServer = async () => {
      try {
        await axios.get(`${apiUrl}/`);
        setServerStatus('online');
      } catch (err) {
        console.error("Server Health Check Failed:", err);
        setServerStatus('offline');
      }
    };
    checkServer();
    // Poll every 10 seconds to keep status live
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
      // Extract detailed error message if available
      const backendMsg = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError(`Failed to process: ${backendMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <header className="mb-12 text-center animate-fade-in relative">
          {/* Server Status Indicator */}
          <div className="absolute top-0 right-0 flex items-center space-x-2 bg-white/5 px-3 py-1 rounded-full border border-white/10">
            <div className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : serverStatus === 'offline' ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'}`}></div>
            <span className="text-xs text-gray-400 font-mono tracking-wider uppercase">
              {serverStatus === 'online' ? 'System Online' : serverStatus === 'offline' ? 'Backend Disconnected' : 'Syncing...'}
            </span>
          </div>

          <h1 className="text-5xl font-black tracking-tight mb-4 mt-8">
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
            {/* Disable upload if server is offline */}
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
