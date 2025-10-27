import { useState, useEffect } from 'react';

export default function DeviceStatus() {
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDeviceInfo = async () => {
      try {
        const response = await fetch('/api/device/');
        if (response.ok) {
          const data = await response.json();
          setDeviceInfo(data);
        }
      } catch (err) {
        console.error('Failed to fetch device info:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch initially
    fetchDeviceInfo();

    // Refresh every 10 seconds
    const interval = setInterval(fetchDeviceInfo, 10000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="absolute top-4 right-4 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-lg px-4 py-2 text-xs font-mono z-50">
        <span className="text-gray-400">Loading...</span>
      </div>
    );
  }

  if (!deviceInfo) {
    return null;
  }

  const isGPU = deviceInfo.device === 'cuda' || deviceInfo.device === 'GPU';
  const faceIsGPU = deviceInfo.face_detection_device?.includes('GPU') || deviceInfo.face_detection_device?.includes('CUDA');

  return (
    <div className="absolute top-4 right-4 bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg px-4 py-2.5 text-xs font-mono z-50 shadow-lg">
      <div className="flex flex-col gap-1.5">
        {/* YOLO Detection Device */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400 min-w-[80px]">YOLO:</span>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isGPU ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
            <span className={`font-semibold ${isGPU ? 'text-green-400' : 'text-yellow-400'}`}>
              {deviceInfo.device?.toUpperCase() || 'CPU'}
            </span>
            {isGPU && deviceInfo.device_name && (
              <span className="text-gray-500 text-[10px]">({deviceInfo.device_name})</span>
            )}
          </div>
        </div>

        {/* Face Detection Device */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400 min-w-[80px]">Face:</span>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${faceIsGPU ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
            <span className={`font-semibold ${faceIsGPU ? 'text-green-400' : 'text-yellow-400'}`}>
              {deviceInfo.face_detection_device || 'CPU'}
            </span>
          </div>
        </div>

        {/* GPU Memory (if available) */}
        {isGPU && deviceInfo.gpu_memory && (
          <div className="flex items-center gap-2 pt-1 border-t border-gray-700">
            <span className="text-gray-400 min-w-[80px]">VRAM:</span>
            <span className="text-blue-400 font-semibold">
              {deviceInfo.gpu_memory.used_gb?.toFixed(1) || 'N/A'} GB / {deviceInfo.gpu_memory.total_gb?.toFixed(1) || 'N/A'} GB
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
