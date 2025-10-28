import React, { useState, useEffect } from "react";
import { CameraIcon, StopIcon, PhoneIcon, UploadIcon } from "./Icons";

export default function CameraPanel({ onStartWebcam, 
  onStopWebcam, 
  isWebcamActive, 
  onStartIPCamera,
  onStopIPCamera,
  isIPCameraActive }){
    
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [showCameraSelect, setShowCameraSelect] = useState(false);
    const [loading, setLoading] = useState(false);

    // Fetch available cameras
    const fetchCameras = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:8000/cameras/list/');
        const data = await response.json();
        setCameras(data.cameras || []);
        if (data.cameras && data.cameras.length > 0) {
          setSelectedCamera(data.cameras[0].index);
        }
      } catch (error) {
        console.error('Error fetching cameras:', error);
      } finally {
        setLoading(false);
      }
    };

    // Select and start camera
    const selectAndStartCamera = async () => {
      if (selectedCamera === null) return;
      
      setLoading(true);
      try {
        // Select the camera
        const selectResponse = await fetch('http://localhost:8000/cameras/select/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ camera_index: selectedCamera })
        });
        
        if (!selectResponse.ok) {
          throw new Error('Failed to select camera');
        }
        
        // Start webcam stream
        await onStartWebcam();
        setShowCameraSelect(false);
      } catch (error) {
        console.error('Error selecting camera:', error);
        alert('Failed to start selected camera');
      } finally {
        setLoading(false);
      }
    };

    // Open camera selection modal
    const openCameraSelection = async () => {
      await fetchCameras();
      setShowCameraSelect(true);
    };

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
              onClick={openCameraSelection}
              disabled={loading}
            >
              <CameraIcon className="w-4 h-4" /> {loading ? 'Loading...' : 'Select & Start Camera'}
            </button>
          )}

          {/* Camera Selection Modal */}
          {showCameraSelect && (
            <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
              <div className="bg-green-950 border-2 border-green-500 p-6 rounded-lg max-w-md w-full mx-4">
                <h3 className="text-green-300 font-bold text-lg mb-4">Select Camera</h3>
                
                {cameras.length === 0 ? (
                  <p className="text-gray-400 mb-4">No cameras detected</p>
                ) : (
                  <div className="space-y-2 mb-4">
                    {cameras.map((camera) => (
                      <label
                        key={camera.index}
                        className={`flex items-center gap-3 p-3 border rounded cursor-pointer transition ${
                          selectedCamera === camera.index
                            ? 'border-green-400 bg-green-900'
                            : 'border-green-700 hover:border-green-500'
                        }`}
                      >
                        <input
                          type="radio"
                          name="camera"
                          value={camera.index}
                          checked={selectedCamera === camera.index}
                          onChange={() => setSelectedCamera(camera.index)}
                          className="w-4 h-4"
                        />
                        <div className="flex-1">
                          <div className="text-green-200 font-medium">{camera.name}</div>
                          <div className="text-gray-400 text-sm">{camera.resolution}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    className="flex-1 bg-black border border-green-600 py-2 hover:bg-green-900 transition text-sm"
                    onClick={selectAndStartCamera}
                    disabled={selectedCamera === null || loading}
                  >
                    {loading ? 'Starting...' : 'Start Selected Camera'}
                  </button>
                  <button
                    className="flex-1 bg-black border border-red-600 py-2 hover:bg-red-900 transition text-sm"
                    onClick={() => setShowCameraSelect(false)}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
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