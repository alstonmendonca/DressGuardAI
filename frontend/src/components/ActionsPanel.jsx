import React, { useState, useEffect } from "react";
import { SaveIcon, AlertIcon, DashboardIcon, FileTextIcon } from "./Icons";

export default function ActionsPanel({ onOpenDashboard, onOpenReportGenerator }){
    const [loggingEnabled, setLoggingEnabled] = useState(false);
    const [loading, setLoading] = useState(false);

    // Fetch logging status on mount
    useEffect(() => {
        fetchLoggingStatus();
    }, []);

    const fetchLoggingStatus = async () => {
        try {
            const response = await fetch("/api/logging/status/");
            if (response.ok) {
                const data = await response.json();
                setLoggingEnabled(data.logging_enabled);
            }
        } catch (err) {
            console.error("Failed to fetch logging status:", err);
        }
    };

    const toggleLogging = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/logging/toggle/", {
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

    return(
        <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">Actions</h3>
          
          {/* Logging Toggle Button */}
          <button 
            onClick={toggleLogging}
            disabled={loading}
            className={`border py-1 sm:py-2 hover:opacity-80 transition text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 ${
                loggingEnabled 
                    ? 'bg-red-900 border-red-500 text-red-200 hover:bg-red-800' 
                    : 'bg-green-900 border-green-600 text-green-200 hover:bg-green-800'
            } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <SaveIcon className="w-4 h-4" />
            {loading ? 'Processing...' : loggingEnabled ? 'Stop Logging' : 'Start Logging'}
          </button>

          <button 
            onClick={onOpenReportGenerator}
            className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2"
          >
            <FileTextIcon className="w-4 h-4" />
            Generate Report
          </button>
          <button className="bg-black border border-green-600 py-1 sm:py-2 hover:bg-green-900 transition text-xs sm:text-sm flex items-center justify-center gap-2">
            <AlertIcon className="w-4 h-4" />
            Set Alerts
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