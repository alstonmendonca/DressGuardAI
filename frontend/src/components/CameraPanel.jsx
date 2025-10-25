import React from "react";
import { CameraIcon, StopIcon, PhoneIcon, UploadIcon } from "./Icons";

export default function CameraPanel({ onStartWebcam, 
  onStopWebcam, 
  isWebcamActive, 
  onStartIPCamera,
  onStopIPCamera,
  isIPCameraActive }){
    return(
        <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">Camera</h3>
          
          {isWebcamActive ? (
            <button
              className="bg-black border border-red-600 py-1 sm:py-2 hover:bg-red-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
              onClick={onStopWebcam}
            >
              <StopIcon className="w-4 h-4" /> Stop Webcam
            </button>
          ) : (
            <button
              className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
              onClick={onStartWebcam}
            >
              <CameraIcon className="w-4 h-4" /> Start Webcam
            </button>
          )}

          {isIPCameraActive ? (
            <button onClick={onStopIPCamera} className="flex items-center justify-center gap-2">
              <StopIcon className="w-4 h-4" /> Stop IP Camera
            </button>
          ) : (
            <button onClick={onStartIPCamera} className="flex items-center justify-center gap-2">
              <PhoneIcon className="w-4 h-4" /> Start Phone Camera
            </button>
          )}

          
          
          <button className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm">
            Camera-1
          </button>
          <button className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm">
            Camera-2
          </button>
          <button
            className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
            onClick={() => document.querySelector('input[type="file"]').click()}
          >
            <UploadIcon className="w-4 h-4" /> Upload Media
          </button>
        </div>
    );
}