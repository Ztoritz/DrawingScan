import React from 'react';

const ResultsList = ({ data }) => {
    if (!data || data.length === 0) {
        return (
            <div className="w-full text-center p-12 glass-panel animate-slide-up mt-8 border border-white/5">
                <div className="inline-flex p-4 rounded-full bg-white/5 mb-4 animate-pulse">
                    <span className="text-4xl">🔍</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">No Features Detected</h3>
                <p className="text-gray-400">
                    The AI couldn't find any clear dimensions.
                    <br /><span className="text-sm opacity-60">Try a clearer image or a different drawing.</span>
                </p>
            </div>
        );
    }

    // Sort: Dimensions first, then GD&T
    const sortedData = [...data].sort((a, b) => {
        if (a.type === b.type) return 0;
        return a.type === 'Dimension' ? -1 : 1;
    });

    const GDTFrame = ({ item }) => (
        <div className="inline-flex items-center border-2 border-black bg-white text-black font-mono font-bold text-sm select-all">
            {/* Symbol Box */}
            <div className="px-2 py-1 border-r-2 border-black min-w-[30px] text-center">
                {getGDTSymbol(item.subtype)}
            </div>
            {/* Value Box */}
            <div className="px-2 py-1 border-r-2 border-black">
                {item.value}
            </div>
            {/* Datum Box */}
            {item.datum && (
                <div className="px-2 py-1 bg-white">
                    {item.datum}
                </div>
            )}
        </div>
    );

    const getGDTSymbol = (subtype) => {
        const map = {
            'Concentricity': '◎',
            'Position': '⌖',
            'Perpendicularity': '⏊',
            'Parallelism': '∥',
            'Flatness': '⏥',
            'Straightness': '—',
            'Cylindricity': '⌭',
            'Profile of Surface': '⏦'
        };
        // Return mapped symbol or first letter if unknown
        return map[subtype] || subtype?.charAt(0) || '?';
    };

    return (
        <div className="w-full animate-slide-up">
            <div className="flex justify-between items-end mb-6">
                <h2 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500 uppercase tracking-tighter">
                    Extracted Data
                </h2>
                <div className="text-xs font-mono text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 rounded">
                    CONFIDENCE: HIGH
                </div>
            </div>

            <div className="glass-panel overflow-hidden border border-white/10 rounded-xl shadow-2xl">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-white/5 border-b border-white/10 text-xs uppercase tracking-wider text-gray-400">
                            <th className="p-4 font-medium">Type</th>
                            <th className="p-4 font-medium">Subtype</th>
                            <th className="p-4 font-medium">Measured Value</th>
                            <th className="p-4 font-medium">Tolerance / Datum</th>
                            <th className="p-4 font-medium text-right">Preview</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {sortedData.map((item, idx) => (
                            <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                <td className="p-4">
                                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${item.type === 'GD&T'
                                            ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                                            : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                                        }`}>
                                        {item.type}
                                    </span>
                                </td>
                                <td className="p-4 text-gray-300 font-medium">
                                    {item.subtype}
                                </td>
                                <td className="p-4">
                                    <span className="font-mono text-lg font-bold text-white tracking-wide">
                                        {item.value}
                                    </span>
                                </td>
                                <td className="p-4">
                                    {item.type === 'GD&T' ? (
                                        <div className="flex items-center gap-2">
                                            <span className="text-gray-400 text-xs">DATUM:</span>
                                            <b className="text-white">{item.datum || '-'}</b>
                                        </div>
                                    ) : (
                                        <span className={`font-mono text-sm px-2 py-1 rounded ${item.tolerance === 'Basic'
                                                ? 'border border-white text-white'
                                                : 'bg-white/10 text-gray-300'
                                            }`}>
                                            {item.tolerance}
                                        </span>
                                    )}
                                </td>
                                <td className="p-4 text-right">
                                    {item.type === 'GD&T' ? (
                                        <GDTFrame item={item} />
                                    ) : (
                                        <div className="text-xs text-gray-600 font-mono">
                                            {item.original_text}
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 text-center">
                <button onClick={() => window.print()} className="text-xs text-gray-500 hover:text-white transition-colors underline decoration-dotted">
                    Export to PDF / Print Report
                </button>
            </div>
        </div>
    );
};

export default ResultsList;
