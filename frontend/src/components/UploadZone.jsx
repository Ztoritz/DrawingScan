import React, { useState, useRef } from 'react';

const UploadZone = ({ onFileSelected }) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            validateAndPass(file);
        }
    };

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            validateAndPass(e.target.files[0]);
        }
    };

    const validateAndPass = (file) => {
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid PDF or Image file.');
            return;
        }
        onFileSelected(file);
    };

    return (
        <div
            className={`relative group cursor-pointer overflow-hidden transition-all duration-500 ease-out
                 glass-panel border-2 border-dashed flex flex-col items-center justify-center p-12
                 ${isDragOver ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/10 hover:border-white/20 hover:bg-white/5'}
      `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleChange}
                accept=".pdf,.jpg,.jpeg,.png,.tiff,.webp"
                className="hidden"
            />

            <div className={`p-4 rounded-full bg-gradient-to-tr from-primary/20 to-secondary/20 mb-6 
                      group-hover:scale-110 transition-transform duration-500 shadow-[0_0_30px_rgba(59,130,246,0.2)]`}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-primary group-hover:text-white transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
            </div>

            <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-primary transition-colors">
                Upload Dimensions PDF or Image
            </h3>
            <p className="text-gray-400 text-sm text-center max-w-md">
                Drag & drop your engineering drawing here, or <span className="text-primary hover:underline">browse</span> to select.
                <br /><span className="text-xs opacity-60 mt-2 block">Supported formats: PDF, JPG, PNG, TIFF, WEBP</span>
            </p>

            {/* Glow effect on hover */}
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>
    );
};

export default UploadZone;
