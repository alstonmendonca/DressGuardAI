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
import { logComplianceResults } from './utils/complianceLogger';

function App() {
  // State to store the uploaded image as a blob URL
  const [imageURL, setImageURL] = useState(null);

  // State to store detection results: [{ class, bbox, confidence }, ...]
  const [detections, setDetections] = useState([]);
  const [activeFeed, setActiveFeed] = useState(null); // 'image', 'webcam', 'video'

  const [currentModel, setCurrentModel] = useState("best"); // Default to your best model
  const [availableModels, setAvailableModels] = useState([]); // Will store available models

  const [complianceInfo, setComplianceInfo] = useState({
    isCompliant: true,
    nonCompliantItems: []
  });

  // References to DOM elements: canvas for drawing, img for size measurement
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const videoRef = useRef(null);
  const videoStream = useRef(null);
  const isDetecting = useRef(false); // FPS limiter
  const hiddenCanvasRef = useRef(null);

  // Add this throttle variable at the top of your component
  const lastWebcamLogTime = useRef(0);
  const WEB_CAM_LOG_INTERVAL = 3000; // Log every 3 seconds

  const lastDetectionUpdate = useRef(0);
  const DETECTION_UPDATE_INTERVAL = 8000; // ms

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
    if ((activeFeed === "image" || activeFeed === "video") && detections.length > 0) {
      requestAnimationFrame(() =>
        drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })
      );
    }
  }, [detections, activeFeed]);

  useEffect(() => {
    // Fetch available models when component mounts
    const fetchModels = async () => {
      try {
        // First get current model
        const currentResponse = await fetch("/api/current-model/");
        if (currentResponse.ok) {
          const currentData = await currentResponse.json();
          setCurrentModel(currentData.current_model);
        }
        
        // Then get available models (you might need to create this endpoint)
        // Alternatively, you can hardcode the available models for now
        const availableModelsList = ["best", "yolov8n"]; // Add your actual available models
        setAvailableModels(availableModelsList);
        
      } catch (err) {
        console.error("Failed to fetch models:", err);
        // Fallback to hardcoded available models
        setAvailableModels(["best", "yolov8n"]);
      }
    };
    
    fetchModels();
  }, []);


  const startWebcam = () => {
    console.log("1. startWebcam called");
    setActiveFeed('webcam');
    setDetections([]);
    isDetecting.current = false;
  };

  const stopWebcam = () => {
    console.log("Stopping webcam...");
    
    // Stop the detection loop
    isDetecting.current = true; // This will prevent new detections
    
    // Stop the video stream
    if (videoStream.current) {
      videoStream.current.getTracks().forEach(track => track.stop());
      videoStream.current = null;
    }
    
    // Clear the video element
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    // Reset state
    setActiveFeed(null);
    setDetections([]);
    
    console.log("Webcam stopped");
  };

  const setupWebcamStream = async () => {
    console.log("3. setupWebcamStream running");
    const video = videoRef.current;
    if (!video) {
      console.warn("Video element not ready");
      return;
    }

    // Stop existing stream
    if (videoStream.current) {
      videoStream.current.getTracks().forEach(t => t.stop());
    }

    try {
      console.log("4. Requesting webcam access...");
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      console.log("5. Webcam access granted", stream);
      videoStream.current = stream;
      video.srcObject = stream;

      video.onloadedmetadata = () => {
        console.log("6. Metadata loaded, playing video...");
        video.play().catch(err => console.error("Play failed:", err));
        requestAnimationFrame(captureAndDetectLoop);
      };
    } catch (err) {
      console.error("Webcam access denied:", err);
      alert("Unable to access camera. Check permissions.");
      setActiveFeed(null);
    }
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

    if (!videoStream.current) {
      console.log("Detection loop stopped - no active stream");
      return;
    }
    
    const video = videoRef.current;
    const hiddenCanvas = hiddenCanvasRef.current;
    const overlayCanvas = canvasRef.current;

    if (!video || !hiddenCanvas || !overlayCanvas || !video.srcObject || video.readyState < 3) {
      console.warn("Video not ready", { video: !!video, canvas: !!hiddenCanvas, srcObject: !!video?.srcObject, readyState: video?.readyState });
      // Not ready, retry
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }

    if (isDetecting.current) {
      requestAnimationFrame(captureAndDetectLoop);
      return;
    }

    isDetecting.current = true;

    hiddenCanvas.width = video.videoWidth;
    hiddenCanvas.height = video.videoHeight;
    const ctx = hiddenCanvas.getContext("2d");
    ctx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);

    hiddenCanvas.toBlob(async (blob) => {
      if (!blob) {
        console.warn("toBlob returned null");
        isDetecting.current = false;
        requestAnimationFrame(captureAndDetectLoop);
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "webcam-frame.jpg");
      formData.append("model", currentModel);  // Add current model to request
      

      try {
        const response = await fetch("/api/detect/", {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections: data.clothes_detected });

          const now = Date.now();

          // Smooth update: only update if detection results are significantly different
          if (now - lastDetectionUpdate.current > DETECTION_UPDATE_INTERVAL) {
            // Check if the new detections are different enough to warrant an update
            const shouldUpdate = shouldUpdateDetections(data.clothes_detected, detections);
            
            if (shouldUpdate) {
              setDetections(data.clothes_detected);
              setComplianceInfo({
                isCompliant: data.compliant,
                nonCompliantItems: data.non_compliant_items || []
              });
            }
            
            lastDetectionUpdate.current = now;
          }


          // ✅ THROTTLED LOGGING FOR WEBCAM
          now = Date.now();
          if (now - lastWebcamLogTime.current > WEB_CAM_LOG_INTERVAL) {
            logComplianceResults(data, "Webcam");
            lastWebcamLogTime.current = now;
          }
        }
      } catch (err) {
        console.error("Webcam detection error:", err);
      } finally {
        isDetecting.current = false;
        setTimeout(() => requestAnimationFrame(captureAndDetectLoop), 100); 
      }

      requestAnimationFrame(captureAndDetectLoop);
    }, "image/jpeg", 0.7);
  };

  // Helper function to determine if detections are significantly different
const shouldUpdateDetections = (newDetections, currentDetections) => {
  if (newDetections.length !== currentDetections.length) return true;
  
  // Check if any detection class or confidence has changed significantly
  for (let i = 0; i < newDetections.length; i++) {
    const newDet = newDetections[i];
    const currentDet = currentDetections[i];
    
    if (!currentDet || 
        newDet.class !== currentDet.class || 
        Math.abs(newDet.confidence - currentDet.confidence) > 0.1) {
      return true;
    }
  }
  
  return false;
};

  const handleModelChange = async (modelName) => {
  try {
    // Convert to lowercase and ensure it matches your MODEL_PATHS
    const modelToSend = modelName.toLowerCase();
    
    const response = await fetch("/api/switch-model/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model_name: modelToSend }),
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
            <option value="best">Initial Model</option>
            <option value="yolov8n">YOLOv8 Nano</option>
            <option value="final">Final Model</option>
            {/* Add more options as needed */}
          </select>
        </div>
      </div>
      

      {/* Main Grid: 3 columns */}
      <div className="min-h-screen bg-black text-green-400 font-mono grid grid-cols-3 gap-2">

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
        />

        {/* === PANEL 5: System Status (Bottom Center) === */}
        <StatusPanel currentModel={currentModel}/>

        {/* === PANEL 6: Settings & Export (Bottom Right) === */}
        <ActionsPanel/>

        <ModelPanel 
          currentModel={currentModel}
          onModelChange={handleModelChange}
        />

      </div>
    </div>
  );
}

export default App;