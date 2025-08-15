// App.jsx - Frontend for DressGuard AI
// This component handles image upload, sends it to the backend for YOLOv8 detection,
// and draws bounding boxes on a canvas over the image.
// Uses React hooks: useState, useRef, useEffect for state and DOM manipulation.
import { useState, useRef, useEffect } from 'react';
import drawBoxes from './utils/drawBoxes';
import captureAndDetect from './utils/captureAndDetect';
import detectFrameFromVideo from './utils/detectFrameFromVideo';
import './App.css';
import CameraPanel from './components/CameraPanel';
import StatusPanel from './components/StatusPanel';
import ActionsPanel from './components/ActionsPanel';

function App() {
  // State to store the uploaded image as a blob URL
  const [imageURL, setImageURL] = useState(null);

  // State to store detection results: [{ class, bbox, confidence }, ...]
  const [detections, setDetections] = useState([]);

  // References to DOM elements: canvas for drawing, img for size measurement
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  const [activeFeed, setActiveFeed] = useState(null); // 'image', 'webcam', 'video'
  const videoRef = useRef(null);
  const videoStream = useRef(null);
  const isDetecting = useRef(false); // FPS limiter

  useEffect(() => {
    return () => {
      if (videoRef.current) {
        videoRef.current.removeEventListener('timeupdate', () => {
          detectFrameFromVideo({imageRef,videoRef, activeFeed, canvasRef, isDetecting, setDetections, drawBoxes, detections})
        });
      }
      if (videoStream.current) {
        videoStream.current.getTracks().forEach(t => t.stop());
      }
      if (imageURL) {
        URL.revokeObjectURL(imageURL);
      }
    };
  }, [imageURL]);

  useEffect(() => {
    return () => {
      if (imageURL) URL.revokeObjectURL(imageURL);
    };
  }, [imageURL]);

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
  useEffect(() => {
    if (detections.length > 0) {
      requestAnimationFrame(() => 
        drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })
      );

    }
  }, [detections]);

  const startWebcam = async () => {
    setActiveFeed('webcam');
    setDetections([]);
    isDetecting.current = false;

    const video = videoRef.current;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoStream.current = stream;
      video.srcObject = stream;

      video.onloadedmetadata = () => {
        video.play();
        requestAnimationFrame(() => {
          captureAndDetect({videoRef, canvasRef, isDetecting, setDetections, drawBoxes})
        }); // Start loop
      };
    } catch (err) {
      console.error("Webcam access denied:", err);
      alert("Unable to access camera. Check permissions.");
      setActiveFeed(null);
    }
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
        <div className="col-span-2 row-span-1 relative border-4 border-green-500 shadow-lg rounded overflow-hidden">
          {activeFeed === 'image' && imageURL ? (
            <>
              <img
                src={imageURL}
                alt="Uploaded"
                ref={imageRef}
                onLoad={() => detections.length > 0 && drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })}
                className="w-full h-auto"
              />
              <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none"  />
            </>
          ) : activeFeed === 'video' && imageURL ? (
            <>
              <video
                ref={videoRef}
                src={imageURL}
                className="w-full h-auto"
                onLoadedMetadata={(e) => {
                  e.target.play();
                  e.target.addEventListener('timeupdate', () => {
                    detectFrameFromVideo({imageRef, videoRef, activeFeed,canvasRef, isDetecting, setDetections, drawBoxes, detections })
                  });
                }}
                onEnded={() => (isDetecting.current = false)}
                playsInline
                autoPlay
              />
              <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
            </>
          ) : activeFeed === 'webcam' ? (
            <>
              <video ref={videoRef} autoPlay muted playsInline className="w-full h-auto" />
              <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
            </>
          ) : (
            <div className="w-full h-64 bg-black flex items-center justify-center">
              <span className="text-green-600">Upload an image or video</span>
            </div>
          )}
        </div>

        {/* === DETECTION LIST (right column, top) === */}
        <div className="row-span-1 bg-green-950 p-4 rounded shadow-lg text-left text-sm h-full flex flex-col">
          <h2 className="text-xl font-bold border-b border-green-400 mb-2">Detected Items:</h2>
          
          {detections.length > 0 ? (
            <ul className="list-disc pl-6 space-y-1 flex-1">
              {detections.map((det, index) => (
                <li key={index}>
                  <span className="font-bold">{det.class}</span> – {det.confidence.toFixed(2)}%
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-green-600 italic text-center py-4 flex-1 flex items-center justify-center">
              No items detected
            </p>
          )}
        </div>

        {/* === PANEL 4: Allows to choose from different camera feeds*/}
        <CameraPanel/>

        {/* === PANEL 5: System Status (Bottom Center) === */}
        <StatusPanel/>

        {/* === PANEL 6: Settings & Export (Bottom Right) === */}
        <ActionsPanel/>

      </div>
    </div>
  );
}

export default App;