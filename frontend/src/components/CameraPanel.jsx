import React from "react";

export default function CameraPanel({ onStartWebcam, onStopWebcam, isWebcamActive }){
    return(
        <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">Camera</h3>
          
          {isWebcamActive ? (
            <button
              className="bg-black border border-red-600 py-1 sm:py-2 hover:bg-red-900 transition text-xs sm:text-sm"
              onClick={onStopWebcam}
            >
              🔴 Stop Webcam
            </button>
          ) : (
            <button
              className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm"
              onClick={onStartWebcam}
            >
              🎥 Start Webcam
            </button>
          )}
          
          <button className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm">
            Camera-1
          </button>
          <button className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm">
            Camera-2
          </button>
          <button
            className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm"
            onClick={() => document.querySelector('input[type="file"]').click()}
          >
            Upload Media
          </button>
        </div>
    );
}