import React, { useState, useEffect } from "react";

export default function StatusPanel(){
    const [systemStatus, setSystemStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch initial status
        fetchSystemStatus();
        
        // Poll every 2 seconds for real-time updates
        const interval = setInterval(fetchSystemStatus, 2000);
        
        return () => clearInterval(interval);
    }, []);

    const fetchSystemStatus = async () => {
        try {
            const response = await fetch("/api/system/status/");
            if (response.ok) {
                const data = await response.json();
                setSystemStatus(data);
                setLoading(false);
            }
        } catch (err) {
            console.error("Failed to fetch system status:", err);
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
                <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">System Status</h3>
                <div className="text-center text-green-400 text-xs">Loading...</div>
            </div>
        );
    }

    if (!systemStatus) {
        return (
            <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
                <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">System Status</h3>
                <div className="text-center text-red-400 text-xs">Failed to load</div>
            </div>
        );
    }

    const { model, logging, database, system, gpu, webcam } = systemStatus;

    return(
        <div className="bg-green-950 border border-green-500 p-2 sm:p-3 md:p-4 rounded flex flex-col gap-2 sm:gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-2 sm:mb-3 md:mb-4 text-sm sm:text-base">System Status</h3>
          
          {/* Model Status */}
          <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
            <div className="flex justify-between items-center">
                <span className="text-green-400">AI Model:</span>
                <span className={`font-semibold ${model.status === 'Active' ? 'text-green-300' : 'text-red-300'}`}>
                    {model.status}
                </span>
            </div>
            <div className="text-green-500 text-[10px] sm:text-xs mt-1">
                {model.device} • {model.name}
            </div>
          </div>

          {/* Webcam Status */}
          <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
            <div className="flex justify-between items-center">
                <span className="text-green-400">Camera:</span>
                <span className={`font-semibold ${webcam.status === 'Active' ? 'text-green-300' : 'text-yellow-300'}`}>
                    {webcam.status}
                </span>
            </div>
          </div>

          {/* Logging Status */}
          <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
            <div className="flex justify-between items-center">
                <span className="text-green-400">Logging:</span>
                <span className={`font-semibold ${logging.enabled ? 'text-green-300' : 'text-red-300'}`}>
                    {logging.enabled ? 'Enabled' : 'Disabled'}
                </span>
            </div>
            <div className="text-green-500 text-[10px] sm:text-xs mt-1">
                Today: {logging.today_violations} • Total: {logging.total_violations}
            </div>
          </div>

          {/* Students Enrolled */}
          <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
            <div className="flex justify-between items-center">
                <span className="text-green-400">Students:</span>
                <span className="font-semibold text-green-300">
                    {database.students_enrolled} Enrolled
                </span>
            </div>
          </div>

          {/* CPU & Memory */}
          <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
            <div className="flex justify-between items-center">
                <span className="text-green-400">CPU Usage:</span>
                <span className="font-semibold text-green-300">{system.cpu_usage}</span>
            </div>
            <div className="flex justify-between items-center mt-1">
                <span className="text-green-400">Memory:</span>
                <span className="font-semibold text-green-300">{system.memory_usage}</span>
            </div>
          </div>

          {/* GPU Info (if available) */}
          {gpu && (
            <div className="bg-black border border-green-600 py-1 sm:py-2 px-2 sm:px-3 text-xs sm:text-sm">
              <div className="text-green-400 font-semibold mb-1">GPU:</div>
              <div className="text-green-500 text-[10px] sm:text-xs">
                {gpu.name}
              </div>
              <div className="text-green-500 text-[10px] sm:text-xs mt-1">
                {gpu.memory_allocated} / {gpu.memory_total}
              </div>
            </div>
          )}
        </div>
    );
}