import React from "react";

export default function CameraPanel({ onStartWebcam }){
    return(
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">Camera</h3>
          <button
            className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs"
            onClick={onStartWebcam}
          >
            🎥 Webcam
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            Camera-1
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            Camera-2
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            Camera-3
          </button>
          <button
            className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs"
            onClick={() => document.querySelector('input[type="file"]').click()}
          >
            📁 Upload Media
          </button>
        </div>
    );
}