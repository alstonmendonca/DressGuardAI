import { useState, useRef, useEffect } from 'react';
import drawBoxes from './utils/drawBoxes';
import detectFrameFromVideo from './utils/detectFrameFromVideo';
import './App.css';
import CameraPanel from './components/CameraPanel';
import StatusPanel from './components/StatusPanel';
import ActionsPanel from './components/ActionsPanel';
import DetectionList from './components/DetectionList';
import MainFeed from "./components/MainFeed";
import ModelPanel from './components/ModelPanel';
import CompliancePanel from './components/CompliancePanel';
import DeviceStatus from './components/DeviceStatus';
import { logComplianceResults } from './utils/complianceLogger';

function App() {
  // State to store the uploaded image as a blob URL
  const [imageURL, setImageURL] = useState(null);

  // State to store detection results: [{ class, bbox, confidence }, ...]
  const [detections, setDetections] = useState([]);
  const [activeFeed, setActiveFeed] = useState(null); // 'image', 'webcam', 'video'

  const [currentModel, setCurrentModel] = useState("best"); // Default to your best model
  const [availableModels, setAvailableModels] = useState([]); // Dynamically loaded models

  const [complianceInfo, setComplianceInfo] = useState({
    isCompliant: true,
    nonCompliantItems: []
  });

  // References to DOM elements: canvas for drawing, img for size measurement
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const videoRef = useRef(null);
  const videoStream = useRef(null);
  const isDetecting = useRef(false); // Prevent concurrent detections
  const hiddenCanvasRef = useRef(null);

  // Throttle logging only (not detection)
  const lastWebcamLogTime = useRef(0);
  const WEB_CAM_LOG_INTERVAL = 3000; // Log every 3 seconds
  
  // Smart throttling for webcam frame capture
  const lastFrameTime = useRef(0);
  const FRAME_INTERVAL = 150; // 150ms between frames (~6-7 FPS for detection, smooth for webcam)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (videoStream.current) {
        videoStream.current.getTracks().forEach(t => t.stop());
      }
      if (imageURL) {
        URL.revokeObjectURL(imageURL);
      }
    };
  }, [imageURL]);

  useEffect(() => {
    // Only draw boxes for image/video modes and webcam mode
    // For webcam, we'll draw in the detection loop for synchronization
    if (activeFeed && detections.length > 0) {
      requestAnimationFrame(() =>
        drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })
      );
    }
  }, [detections, activeFeed]);

  useEffect(() => {
    // Fetch current model and available models when component mounts
    const fetchCurrentModel = async () => {
      try {
        const response = await fetch("/api/current-model/");
        if (response.ok) {
          const data = await response.json();
          setCurrentModel(data.current_model);
          console.log("Current model:", data.current_model);
        }
      } catch (err) {
        console.error("Failed to fetch current model:", err);
      }
    };
    
    const fetchAvailableModels = async () => {
      try {
        const response = await fetch("/api/models/");
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(data.models || []);
          console.log("Available models:", data.models);
        }
      } catch (err) {
        console.error("Failed to fetch available models:", err);
      }
    };
    
    fetchCurrentModel();
    fetchAvailableModels();
  }, []);


  const startIPCamera = (url) => {
  console.log("Starting IP Camera feed:", url);
  setActiveFeed('ipcam');
  setDetections([]);
  isDetecting.current = false;

  const video = videoRef.current;
  if (!video) {
    console.warn("Video element not ready");
    return;
  }

  // Stop any existing stream
  if (videoStream.current) {
    videoStream.current.getTracks().forEach(t => t.stop());
    videoStream.current = null;
  }

  // Assign IP camera stream
  video.srcObject = null;
  video.src = url;
  video.crossOrigin = "anonymous"; // allow canvas to read frames
  video.onloadedmetadata = () => {
    console.log("IP camera metadata loaded");
    video.play().catch(err => console.error("Play failed:", err));
    requestAnimationFrame(captureAndDetectLoop);
  };
};

const stopIPCamera = () => {
  console.log("Stopping IP Camera feed");
  if (videoRef.current) {
    videoRef.current.pause();
    videoRef.current.src = "";
  }
  setActiveFeed(null);
  setDetections([]);
};

  const startWebcam = async () => {
    console.log("Starting backend webcam stream...");
    setActiveFeed('webcam');
    setDetections([]);
    isDetecting.current = false;
    
    // No need to access browser webcam - backend handles it
    // The img element will automatically start displaying the MJPEG stream
  };

  const stopWebcam = async () => {
    console.log("Stopping backend webcam stream...");
    
    try {
      // Tell backend to stop the webcam
      await fetch("/api/webcam/stop/", { method: "POST" });
      console.log("Backend webcam stopped");
    } catch (err) {
      console.error("Error stopping webcam:", err);
    }
    
    // Reset frontend state
    setActiveFeed(null);
    setDetections([]);
    isDetecting.current = false;
    
    console.log("Webcam stopped");
  };

  // Simplified - no longer needed for backend streaming
  const setupWebcamStream = () => {
    // Backend handles webcam access directly
    // This function kept for compatibility but does nothing
    console.log("Using backend webcam stream - no browser webcam access needed");
  };

  /**
   * Handles file upload:
   * - Reads the selected image
   * - Sends it to the FastAPI backend
   * - Receives detections and triggers box drawing
   */
  const handleFileChange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const url = URL.createObjectURL(file);
  setDetections([]);
  isDetecting.current = false;

  if (file.type.startsWith("image/")) {
    setImageURL(url);
    setActiveFeed('image');

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", currentModel);

    try {
      const response = await fetch("/api/detect/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setDetections(data.clothes_detected);
        
        setComplianceInfo({
          isCompliant: data.compliant,
          nonCompliantItems: data.non_compliant_items || []
        });
        
        logComplianceResults(data, "Image");
      }
    } catch (err) {
      console.error("Detection error:", err);
    }
  } 
  else if (file.type.startsWith("video/")) {
    setActiveFeed('video');
    setImageURL(url);
    setDetections([]);
  }
};

  /**
   * Redraw boxes if detections or image URL changes.
   * Acts as a fallback in case onLoad fires before detection completes.
   */
  

  const captureAndDetectLoop = async () => {
    // Only runs for IP camera - webcam uses backend streaming
    if (activeFeed !== "ipcam") {
      console.log("Detection loop stopped - not IP camera");
      return;
    }
    
    const video = videoRef.current;
    const hiddenCanvas = hiddenCanvasRef.current;
    const overlayCanvas = canvasRef.current;

    // Validation with better error handling
    if (!video || !hiddenCanvas || !overlayCanvas) {
      console.warn("Missing required elements");
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }

    // Check video readiness (readyState >= 2 means HAVE_CURRENT_DATA)
    if (!video.srcObject || video.readyState < 2) {
      console.debug("Video not ready", { 
        hasSrcObject: !!video.srcObject, 
        readyState: video.readyState 
      });
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }

    // Check if detection is already in progress
    if (isDetecting.current) {
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }
    
    // Smart throttling - allow frames every 150ms for smooth real-time detection
    const now = Date.now();
    if (now - lastFrameTime.current < FRAME_INTERVAL) {
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }
    lastFrameTime.current = now;

    isDetecting.current = true;

    // Set canvas dimensions to match video
    if (hiddenCanvas.width !== video.videoWidth || hiddenCanvas.height !== video.videoHeight) {
      hiddenCanvas.width = video.videoWidth;
      hiddenCanvas.height = video.videoHeight;
    }

    const ctx = hiddenCanvas.getContext("2d", { alpha: false });
    
    try {
      // Clear and draw video frame
      ctx.clearRect(0, 0, hiddenCanvas.width, hiddenCanvas.height);
      ctx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
    } catch (err) {
      console.error("Failed to draw video frame:", err);
      isDetecting.current = false;
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }

    // Convert to blob with optimized quality
    hiddenCanvas.toBlob(async (blob) => {
      if (!blob) {
        console.warn("toBlob returned null");
        isDetecting.current = false;
        requestAnimationFrame(captureAndDetectLoop);
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "webcam-frame.jpg");
      formData.append("model", currentModel);

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);  // 5 second timeout

      try {
        const response = await fetch("/api/detect/", {
          method: "POST",
          body: formData,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          console.error(`Detection failed (${response.status})`);
          isDetecting.current = false;
          setTimeout(() => requestAnimationFrame(captureAndDetectLoop), 100);
          return;
        }

        const data = await response.json();
        
        // Update detections immediately for real-time response
        // The useEffect will handle drawing boxes
        setDetections(data.clothes_detected);
        setComplianceInfo({
          isCompliant: data.compliant,
          nonCompliantItems: data.non_compliant_items || []
        });

        // Throttled logging for webcam (to avoid console spam)
        const logNow = Date.now();
        if (logNow - lastWebcamLogTime.current > WEB_CAM_LOG_INTERVAL) {
          logComplianceResults(data, "Webcam");
          lastWebcamLogTime.current = logNow;
        }

      } catch (err) {
        clearTimeout(timeoutId);
        
        if (err.name === 'AbortError') {
          console.warn("Detection request timeout");
        } else {
          console.error("Webcam detection error:", err.message);
        }
      } finally {
        isDetecting.current = false;
        // Continue detection loop immediately
        requestAnimationFrame(captureAndDetectLoop);
      }

    }, "image/jpeg", 0.75);  // Optimized JPEG quality
  };

  const handleModelChange = async (modelName) => {
  try {
    // Send the model name as-is (backend handles case-insensitive matching)
    const response = await fetch("/api/switch-model/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model_name: modelName }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Switch failed:", errorData);
      return;
    }

    const data = await response.json();
    setCurrentModel(data.current_model);
    
    // Refresh detection if active
    if (activeFeed === 'image' && imageURL) {
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput?.files[0]) {
        handleFileChange({ target: { files: [fileInput.files[0]] } });
      }
    }
  } catch (err) {
    console.error("Model switch error:", err);
  }
};

  return (
    <div className="p-0">
      <h1 className="bg-black text-green-400 font-mono text-xl sm:text-2xl md:text-3xl mb-4 md:mb-6 border-b-2 pb-2 border-green-400 tracking-widest uppercase w-full text-center px-2">
        DressGuard AI
      </h1>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 md:gap-4 mb-4 md:mb-6 px-2">
        {/* File input */}
        <input
          type="file"
          accept="image/*,video/*"  
          onChange={handleFileChange}
          className="bg-green-900 text-green-300 border border-green-400 p-1 sm:p-2 rounded hover:bg-green-800 transition-all cursor-pointer text-xs sm:text-sm w-full sm:w-auto max-w-xs"
        />

        {/* Model selection dropdown */}
        <div className="flex items-center gap-1 sm:gap-2 w-full sm:w-auto justify-center">
          <label htmlFor="model-select" className="text-green-300 text-xs sm:text-sm whitespace-nowrap">
            Model:
          </label>
          <select
            id="model-select"
            value={currentModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="bg-green-900 text-green-300 border border-green-400 p-1 sm:p-2 rounded hover:bg-green-800 transition-all cursor-pointer px-2 text-xs sm:text-sm w-full sm:w-auto"
          >
            {availableModels.length > 0 ? (
              availableModels.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.id} ({model.class_count} classes)
                </option>
              ))
            ) : (
              <option value={currentModel}>{currentModel}</option>
            )}
          </select>
        </div>
      </div>
      

      {/* Main Grid: 3 columns */}
      <div className="min-h-screen bg-black text-green-400 font-mono grid grid-cols-3 gap-2 relative">

        {/* Device Status Indicator - Top Right */}
        <DeviceStatus />

        {/* === MAIN FEED (col-span-2) === */}
        <MainFeed
          activeFeed={activeFeed}
          imageURL={imageURL}
          imageRef={imageRef}
          videoRef={videoRef}
          canvasRef={canvasRef}
          hiddenCanvasRef={hiddenCanvasRef}
          detections={detections}
          drawBoxes={drawBoxes}
          detectFrameFromVideo={detectFrameFromVideo}
          isDetecting={isDetecting}
          setDetections={setDetections}
          setupWebcamStream={setupWebcamStream}   
          onWebcamStreamStart={() => {
            console.log("Starting detection loop");
            requestAnimationFrame(captureAndDetectLoop);
          }}
        />

        {/* === DETECTION LIST (right column, top) === */}
        <DetectionList 
          detections={detections} 
          complianceInfo={complianceInfo}
        />

        {/* === PANEL 4: Allows to choose from different camera feeds*/}
        <CameraPanel 
          onStartWebcam={startWebcam}
          onStopWebcam={stopWebcam}
          isWebcamActive={activeFeed === 'webcam'}
          onStartIPCamera={() => startIPCamera("http://100.68.75.75:8080")} 
          onStopIPCamera={stopIPCamera}
          isIPCameraActive={activeFeed === 'ipcam'}
        />

        {/* === PANEL 5: System Status (Bottom Center) === */}
        <StatusPanel currentModel={currentModel}/>

        {/* === PANEL 6: Settings & Export (Bottom Right) === */}
        <ActionsPanel/>

        {/* === PANEL 7: Model Selection === */}
        <ModelPanel 
          currentModel={currentModel}
          onModelChange={handleModelChange}
        />

        {/* === PANEL 8: Compliance Settings === */}
        <CompliancePanel currentModel={currentModel} />

      </div>
    </div>
  );
}

export default App;