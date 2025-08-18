import React from "react";

export default function ModelPanel({ currentModel, onModelChange }) {
    const models = [
        {
            id: "best",
            name: "Best Model",
            available: true,
            description: "Primary clothing detection model"
        },
        {
            id: "yolov8n", 
            name: "YOLOv8 Nano",
            available: true,
            description: "Lightweight clothing detection"
        },
        {
            id: "yolov10",
            name: "YOLOv10",
            available: false,
            description: "Coming soon"
        },
        {
            id: "yolov12",
            name: "YOLOv12",
            available: false,
            description: "Coming soon"
        }
    ];

    return (
        <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
            <h3 className="text-center font-bold text-green-300 mb-4">AI Model Selection</h3>
            <div className="grid grid-cols-4 gap-2">
                {models.map((model) => (
                    <button
                        key={model.id}
                        className={`bg-black border ${
                            currentModel === model.id 
                                ? 'border-green-400 bg-green-900' 
                                : model.available 
                                    ? 'border-green-600 hover:bg-green-900' 
                                    : 'border-gray-600 text-gray-500 cursor-not-allowed'
                        } py-2 transition text-xs text-center relative group`}
                        onClick={() => model.available && onModelChange(model.id)}
                        disabled={!model.available}
                        title={model.description}
                    >
                        {model.name}
                        {!model.available && (
                            <span className="absolute -top-2 -right-2 bg-gray-700 text-gray-300 text-[8px] px-1 rounded">
                                Soon
                            </span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}