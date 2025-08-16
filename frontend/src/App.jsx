// App.jsx - Frontend for DressGuard AI
// This component handles image upload, sends it to the backend for YOLOv8 detection,
// and draws bounding boxes on a canvas over the image.
// Uses React hooks: useState, useRef, useEffect for state and DOM manipulation.
import { useState, useRef, useEffect } from 'react';
import drawBoxes from './utils/drawBoxes';
import detectFrameFromVideo from './utils/detectFrameFromVideo';
import './App.css';
import CameraPanel from './components/CameraPanel';
import StatusPanel from './components/StatusPanel';
import ActionsPanel from './components/ActionsPanel';
import DetectionList from './components/DetectionList';
import MainFeed from "./components/MainFeed";

function App() {
  // State to store the uploaded image as a blob URL
  const [imageURL, setImageURL] = useState(null);

  // State to store detection results: [{ class, bbox, confidence }, ...]
  const [detections, setDetections] = useState([]);
  const [activeFeed, setActiveFeed] = useState(null); // 'image', 'webcam', 'video'

  // References to DOM elements: canvas for drawing, img for size measurement
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const videoRef = useRef(null);
  const videoStream = useRef(null);
  const isDetecting = useRef(false); // FPS limiter
  const hiddenCanvasRef = useRef(null);

  

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
    if (detections.length > 0) {
      requestAnimationFrame(() => 
        drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })
      );

    }
  }, [detections]);

  const startWebcam = () => {
    console.log("1. startWebcam called");
    setActiveFeed('webcam');
    setWebcamRequested(true); // Just set a flag
    setDetections([]);
    isDetecting.current = false;
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

    try {
      const response = await fetch("http://127.0.0.1:8000/detect/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setDetections(data.clothes_detected);
      }
    } catch (err) {
      console.error("Detection error:", err);
    }
  } 
  else if (file.type.startsWith("video/")) {
    // ✅ Step 1: Set activeFeed FIRST
    setActiveFeed('video');
    setImageURL(url);
    setDetections([]);

    // ✅ Step 2: Use useEffect or wait for render
    // We'll handle src and event listener in JSX via `onLoadedMetadata`
  }
};

  /**
   * Redraw boxes if detections or image URL changes.
   * Acts as a fallback in case onLoad fires before detection completes.
   */
  

  const captureAndDetectLoop = async () => {
    console.log("7. captureAndDetectLoop running");
    const video = videoRef.current;
    const hiddenCanvas = hiddenCanvasRef.current;
    const overlayCanvas = canvasRef.current;

    if (!video || !hiddenCanvas || overlayCanvas || !video.srcObject || video.readyState < 3) {
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
    console.log("8. Capturing frame from webcam");

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

      console.log("9. Frame captured, sending to backend", blob);
      const formData = new FormData();
      formData.append("file", blob, "webcam-frame.jpg");
      

      try {
        const response = await fetch("http://127.0.0.1:8000/detect/", {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          console.log("10. Detection result:", data);
          setDetections(data.clothes_detected);
          drawBoxes({ canvasRef: overlayCanvas, imageRef, videoRef, activeFeed, detections: data.clothes_detected });
        } else{
          console.error("Detection failed:", await response.text());
        }
      } catch (err) {
        console.error("Webcam detection error:", err);
      } finally {
        isDetecting.current = false;
      }

      requestAnimationFrame(captureAndDetectLoop);
    }, "image/jpeg", 0.7);
  };


  return (
    <div className="p-0">
      <h1 className="bg-black text-green-400 font-mono text-3xl mb-6 border-b-2 pb-2 border-green-400 tracking-widest uppercase w-auto">
        DressGuard AI
      </h1>

      {/* File input */}
      <input
        type="file"
        accept="image/*,video/*"  
        onChange={handleFileChange}
        className="mb-6 bg-green-900 text-green-300 border border-green-400 p-2 rounded hover:bg-green-800 transition-all"
      />

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
        <DetectionList detections={detections} />

        {/* === PANEL 4: Allows to choose from different camera feeds*/}
        <CameraPanel onStartWebcam={startWebcam}/>

        {/* === PANEL 5: System Status (Bottom Center) === */}
        <StatusPanel/>

        {/* === PANEL 6: Settings & Export (Bottom Right) === */}
        <ActionsPanel/>

      </div>
    </div>
  );
}

export default App;