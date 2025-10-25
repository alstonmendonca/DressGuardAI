import React, { useState, useEffect } from "react";

export default function ModelPanel({ currentModel, onModelChange }) {
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch available models from backend
    useEffect(() => {
        const fetchModels = async () => {
            try {
                setLoading(true);
                const response = await fetch("/api/models/");
                
                if (!response.ok) {
                    throw new Error("Failed to fetch models");
                }
                
                const data = await response.json();
                
                // Transform backend data to component format (simplified for dynamic discovery)
                const formattedModels = data.models.map(model => ({
                    id: model.id,
                    name: model.id,  // Use ID as name since no display_name
                    available: true,
                    path: model.path,
                    classes: model.classes || [],
                    classCount: model.class_count || 0,
                    isCurrent: model.is_current
                }));
                
                setModels(formattedModels);
                setError(null);
            } catch (err) {
                console.error("Error fetching models:", err);
                setError("Failed to load models");
                
                // Fallback to empty array
                setModels([]);
            } finally {
                setLoading(false);
            }
        };
        
        fetchModels();
    }, []);

    const handleModelClick = (modelId) => {
        const model = models.find(m => m.id === modelId);
        if (model && model.available) {
            // Scroll to top first
            window.scrollTo({ top: 0, behavior: 'smooth' });
            // Then trigger the model change
            onModelChange(modelId);
        }
    };

    // Loading state
    if (loading) {
        return (
            <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
                <h3 className="text-center font-bold text-green-300 mb-4">AI Model Selection</h3>
                <div className="flex items-center justify-center py-8">
                    <div className="text-green-400 animate-pulse">Loading models...</div>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
                <h3 className="text-center font-bold text-green-300 mb-4">AI Model Selection</h3>
                <div className="flex items-center justify-center py-8">
                    <div className="text-red-400">{error}</div>
                </div>
            </div>
        );
    }

    // Empty state
    if (models.length === 0) {
        return (
            <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
                <h3 className="text-center font-bold text-green-300 mb-4">AI Model Selection</h3>
                <div className="flex items-center justify-center py-8">
                    <div className="text-yellow-400">No models found. Add .pt files to the models/ folder</div>
                </div>
            </div>
        );
    }

    return (
        <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
            <h3 className="text-center font-bold text-green-300 mb-4">
                AI Model Selection 
                <span className="text-xs text-green-400 ml-2">
                    ({models.length} model{models.length !== 1 ? 's' : ''} available)
                </span>
            </h3>
            <div className={`grid gap-2 ${
                models.length <= 2 ? 'grid-cols-2' : 
                models.length <= 4 ? 'grid-cols-4' : 
                'grid-cols-4'
            }`}>
                {models.map((model) => (
                    <button
                        key={model.id}
                        className={`bg-black border ${
                            currentModel === model.id 
                                ? 'border-green-400 bg-green-900 shadow-lg shadow-green-500/50' 
                                : model.available 
                                    ? 'border-green-600 hover:bg-green-900 hover:border-green-400' 
                                    : 'border-gray-600 text-gray-500 cursor-not-allowed'
                        } py-2 px-2 transition-all duration-200 text-xs text-center relative group`}
                        onClick={() => handleModelClick(model.id)}
                        disabled={!model.available}
                        title={`${model.name} - ${model.classCount} classes`}
                    >
                        <div className="font-semibold">{model.name}</div>
                        <div className="text-[10px] text-green-400 mt-1">
                            {model.classCount} classes
                        </div>
                        {currentModel === model.id && (
                            <span className="absolute -top-2 -right-2 bg-green-500 text-black text-[8px] px-1.5 py-0.5 rounded font-bold">
                                ACTIVE
                            </span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}