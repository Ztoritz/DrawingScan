import React from 'react';

const ResultsList = ({ data }) => {
    if (!data) return null;

    if (data.length === 0) {
        return (
            <div className="w-full text-center p-8 glass-panel animate-slide-up mt-8">
                <div className="inline-block p-4 rounded-full bg-white/5 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">No Features Detected</h3>
                <p className="text-gray-400 max-w-md mx-auto">
                    We processed the file but couldn't identify any dimensions or GD&T symbols.
                    <br /><span className="text-sm opacity-60">Try uploading a higher quality PDF or Image.</span>
                </p>
            </div>
        );
    }

    const dimensions = data.filter(item => item.type === 'Dimension');
    const gdt = data.filter(item => item.type === 'GD&T');

    return (
        <div className="w-full space-y-8 animate-slide-up">

            {/* Search/Filter Header (Visual only for now) */}
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Extraction Results
                </h2>
                <div className="text-sm text-gray-500 font-mono">
                    {data.length} items found
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Linear Dimensions Column */}
                <div className="glass-panel p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-1 h-6 bg-primary rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                        <h3 className="text-lg font-semibold text-white">Linear Dimensions</h3>
                    </div>

                    <div className="space-y-3">
                        {dimensions.length === 0 ? (
                            <p className="text-gray-500 italic text-sm">No dimensions detected.</p>
                        ) : (
                            dimensions.map((item, idx) => (
                                <div key={idx} className="group flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200">
                                    <div>
                                        <div className="text-2xl font-mono font-bold text-white group-hover:text-primary transition-colors">
                                            {item.value}
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Page {item.page} • Raw: "{item.original_text}"
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className={`text-sm font-mono px-2 py-1 rounded bg-secondary/10 text-secondary border border-secondary/20`}>
                                            {item.tolerance}
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* GD&T Column */}
                <div className="glass-panel p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-1 h-6 bg-accent rounded-full shadow-[0_0_10px_rgba(236,72,153,0.5)]"></div>
                        <h3 className="text-lg font-semibold text-white">GD&T Symbols</h3>
                    </div>

                    <div className="space-y-3">
                        {gdt.length === 0 ? (
                            <p className="text-gray-500 italic text-sm">No GD&T symbols detected.</p>
                        ) : (
                            gdt.map((item, idx) => (
                                <div key={idx} className="group flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-accent font-bold">{item.subtype}</span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Page {item.page}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-gray-400 font-mono bg-black/30 px-2 py-1 rounded">
                                            {item.original_text}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResultsList;
