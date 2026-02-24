import React, { useState, useEffect } from "react";
import { SaveIcon, AlertIcon, DashboardIcon, FileTextIcon } from "./Icons";

export default function ActionsPanel({ 
    onOpenDashboard, 
    onOpenReportGenerator,
    onOpenWhatsAppAlert,
    canLogImage = false,
    isLoggingImage = false,
    onLogImageResult
}){
    const [loggingEnabled, setLoggingEnabled] = useState(false);
    const [faceDetectionEnabled, setFaceDetectionEnabled] = useState(false);
    const [loading, setLoading] = useState(false);
    const [faceLoading, setFaceLoading] = useState(false);
    const [alertLoading, setAlertLoading] = useState(false);
    const [whatsappEnabled, setWhatsappEnabled] = useState(false);

    // Fetch logging and face detection status on mount
    useEffect(() => {
        fetchLoggingStatus();
        fetchFaceDetectionStatus();
        checkWhatsappStatus();
    }, []);

    const fetchLoggingStatus = async () => {
        try {
            const response = await fetch("/logging/status/");
            if (response.ok) {
                const data = await response.json();
                setLoggingEnabled(data.logging_enabled);
            }
        } catch (err) {
            console.error("Failed to fetch logging status:", err);
        }
    };

    const fetchFaceDetectionStatus = async () => {
        try {
            const response = await fetch("/face-detection/status/");
            if (response.ok) {
                const data = await response.json();
                setFaceDetectionEnabled(data.face_detection_enabled);
            }
        } catch (err) {
            console.error("Failed to fetch face detection status:", err);
        }
    };

    const checkWhatsappStatus = async () => {
        try {
            const response = await fetch("/dashboard/whatsapp/status/");
            if (response.ok) {
                const data = await response.json();
                setWhatsappEnabled(data.enabled && data.configured);
            }
        } catch (err) {
            console.error("Failed to check WhatsApp status:", err);
        }
    };

    const toggleLogging = async () => {
        setLoading(true);
        try {
            const response = await fetch("/logging/toggle/", {
                method: "POST",
            });
            if (response.ok) {
                const data = await response.json();
                setLoggingEnabled(data.logging_enabled);
                console.log(data.message);
            }
        } catch (err) {
            console.error("Failed to toggle logging:", err);
        } finally {
            setLoading(false);
        }
    };

    const toggleFaceDetection = async () => {
        setFaceLoading(true);
        try {
            const response = await fetch("/face-detection/toggle/", {
                method: "POST",
            });
            if (response.ok) {
                const data = await response.json();
                setFaceDetectionEnabled(data.face_detection_enabled);
                console.log(data.message);
            }
        } catch (err) {
            console.error("Failed to toggle face detection:", err);
        } finally {
            setFaceLoading(false);
        }
    };

    const handleSendAlerts = () => {
        // Open WhatsApp alert modal instead of directly sending
        if (onOpenWhatsAppAlert) {
            onOpenWhatsAppAlert();
        }
    };

    return(
        <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">Actions</h3>
          
          {/* Log Image Result Button - Only shown when image upload is available to log */}
          {canLogImage && (
            <button 
              onClick={onLogImageResult}
              disabled={isLoggingImage}
              className={`border py-1 sm:py-2 transition text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 bg-yellow-900 border-yellow-500 text-yellow-200 hover:bg-yellow-800 hover:opacity-80 ${
                  isLoggingImage ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              title="Log the uploaded non-compliant image"
            >
              <SaveIcon className="w-4 h-4" />
              {isLoggingImage ? 'Logging...' : 'Log Image Result'}
            </button>
          )}
          
          {/* Logging Toggle Button - For video/camera stream */}
          <button 
            onClick={toggleLogging}
            disabled={loading || canLogImage}
            className={`border py-1 sm:py-2 hover:opacity-80 transition text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 ${
                loggingEnabled 
                    ? 'bg-red-900 border-red-500 text-red-200 hover:bg-red-800' 
                    : 'bg-green-900 border-green-600 text-green-200 hover:bg-green-800'
            } ${(loading || canLogImage) ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={canLogImage ? 'Use Log Image Result button for uploaded images' : 'Toggle logging for video/camera stream'}
          >
            <SaveIcon className="w-4 h-4" />
            {loading ? 'Processing...' : loggingEnabled ? 'Stop Logging (Stream)' : 'Start Logging (Stream)'}
          </button>

          {/* Face Detection Toggle Button */}
          <button 
            onClick={toggleFaceDetection}
            disabled={faceLoading}
            className={`border py-1 sm:py-2 hover:opacity-80 transition text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 ${
                faceDetectionEnabled 
                    ? 'bg-blue-900 border-blue-500 text-blue-200 hover:bg-blue-800' 
                    : 'bg-gray-900 border-gray-600 text-gray-200 hover:bg-gray-800'
            } ${faceLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <AlertIcon className="w-4 h-4" />
            {faceLoading ? 'Processing...' : faceDetectionEnabled ? 'Face Detection ON' : 'Face Detection OFF'}
          </button>

          <button 
            onClick={onOpenReportGenerator}
            className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
          >
            <FileTextIcon className="w-4 h-4" />
            Generate Report
          </button>
          
          <button 
            onClick={handleSendAlerts}
            className="border py-1 sm:py-2 transition text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 bg-green-900 border-green-600 text-green-200 hover:bg-green-800 hover:opacity-80"
            title="Send violation alerts via WhatsApp"
          >
            <AlertIcon className="w-4 h-4" />
            Send Alerts
          </button>
          
          <button 
            onClick={onOpenDashboard}
            className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
          >
            <DashboardIcon className="w-4 h-4" />
            Dashboard
          </button>
        </div>
    );
}