import React from "react";

export default function ModelPanel() {
    return (
        <div className="col-span-3 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3">
            <h3 className="text-center font-bold text-green-300 mb-4">AI Model Selection</h3>
            <div className="grid grid-cols-4 gap-2">
                <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-center">
                    YOLOv8
                </button>
                <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-center">
                    YOLOv10
                </button>
                <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-center">
                    YOLOv11
                </button>
                <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-center">
                    YOLOv12
                </button>
            </div>
        </div>
    );
}