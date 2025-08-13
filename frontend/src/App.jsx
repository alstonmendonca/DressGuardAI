// App.jsx - Frontend for DressGuard AI
// This component handles image upload, sends it to the backend for YOLOv8 detection,
// and draws bounding boxes on a canvas over the image.
// Uses React hooks: useState, useRef, useEffect for state and DOM manipulation.
import { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  // State to store the uploaded image as a blob URL
  const [imageURL, setImageURL] = useState(null);

  // State to store detection results: [{ class, bbox, confidence }, ...]
  const [detections, setDetections] = useState([]);

  // References to DOM elements: canvas for drawing, img for size measurement
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  /**
   * Draws bounding boxes and labels on the canvas based on detection results.
   * Scales coordinates from original image dimensions to displayed size.
   * Also draws a crosshair at the center (UI sniper-scope effect).
   */
  const drawBoxes = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    const img = imageRef.current;

    // Safety check: ensure all required elements are available
    if (!canvas || !ctx || !img) {
      console.warn("Canvas, context, or image not available");
      return;
    }

    // Get the actual rendered size of the image (after browser scales it)
    // Using .width/.height instead of clientWidth ensures correct aspect ratio
    const displayWidth = img.width;
    const displayHeight = img.height;

    // Resize canvas to exactly match the rendered image
    canvas.width = displayWidth;
    canvas.height = displayHeight;

    // Calculate scaling factors from original image → displayed size
    // This allows us to map detection coordinates (from full-res image) to screen
    const scaleX = displayWidth / img.naturalWidth;
    const scaleY = displayHeight / img.naturalHeight;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Style for bounding boxes and text
    ctx.lineWidth = 2;
    ctx.font = "16px monospace";
    ctx.strokeStyle = "#00FF00"; // Neon green
    ctx.fillStyle = "#00FF00";

    // Draw each detected object
    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox; // Bounding box in [left, top, right, bottom]

      // Scale bounding box to fit displayed image size
      const sx1 = x1 * scaleX;
      const sy1 = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      // Draw rectangle
      ctx.strokeRect(sx1, sy1, width, height);

      // Draw label above or below box to avoid going off-screen
      const textY = sy1 > 20 ? sy1 - 5 : sy1 + 20; // If near top, place below
      ctx.fillText(`${det.class} (${Math.round(det.confidence * 100)}%)`, sx1, textY);
    });

    // Draw center crosshair (sniper-style UI for surveillance theme)
    ctx.strokeStyle = "#00FF00";
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2 - 20, canvas.height / 2);
    ctx.lineTo(canvas.width / 2 + 20, canvas.height / 2);
    ctx.moveTo(canvas.width / 2, canvas.height / 2 - 20);
    ctx.lineTo(canvas.width / 2, canvas.height / 2 + 20);
    ctx.stroke();
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

    // Create a temporary URL for previewing the image
    const imageBlobURL = URL.createObjectURL(file);
    setImageURL(imageBlobURL);
    setDetections([]); // Reset previous results

    // Prepare form data to send image to backend
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Send image to YOLOv8 backend
      const response = await fetch("http://127.0.0.1:8000/detect/", {
        method: "POST",
        body: formData,
      });

      // Handle non-200 responses (e.g., server error)
      if (!response.ok) {
        const errorMsg = await response.text();
        console.error("Detection failed:", errorMsg);
        return;
      }

      // Parse JSON response
      const data = await response.json();
      console.log("Detection result:", data);
      setDetections(data.clothes_detected);

      // If image has already loaded, draw boxes immediately
      if (imageRef.current?.complete) {
        console.log("Image already loaded, drawing boxes...");
        drawBoxes();
      }
    } catch (err) {
      // Catch network errors or CORS issues
      console.error("Fetch error (check if backend is running):", err);
    }
  };

  /**
   * Redraw boxes if detections or image URL changes.
   * Acts as a fallback in case onLoad fires before detection completes.
   */
  useEffect(() => {
    if (imageURL && detections.length > 0 && imageRef.current?.complete) {
      console.log("Redrawing boxes (useEffect trigger)");
      drawBoxes();
    }
  }, [imageURL, detections]); // Re-run when image or detections change

  return (
    <div className="p-0">
      <h1 className="bg-black text-green-400 font-mono text-3xl mb-6 border-b-2 pb-2 border-green-400 tracking-widest uppercase w-auto">
        DressGuard AI
      </h1>

      {/* File input */}
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="mb-6 bg-green-900 text-green-300 border border-green-400 p-2 rounded hover:bg-green-800 transition-all"
      />

      {/* Main Grid: 3 columns */}
      <div className="min-h-screen bg-black text-green-400 font-mono grid grid-cols-3 gap-2">

        {/* === MAIN FEED (col-span-2) === */}
        <div className="col-span-2 row-span-1 relative border-4 border-green-500 shadow-lg rounded overflow-hidden">
          {imageURL ? (
            <>
              <img
                src={imageURL}
                alt="Uploaded"
                ref={imageRef}
                onLoad={() => {
                  if (detections.length > 0) drawBoxes();
                }}
                className="w-full h-auto"
              />
              <canvas
                ref={canvasRef}
                className="absolute top-0 left-0 pointer-events-none"
              />
            </>
          ) : (
            <div className="w-full h-64 bg-black flex items-center justify-center">
              <span className="text-green-600">Upload an image to begin</span>
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

        {/* === PANEL 4: Camera Controls (Bottom Left) === */}
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">Camera Controls</h3>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            ▲ Zoom In
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            ▼ Zoom Out
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            ◀ Pan Left
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            ▶ Pan Right
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            ■ Center View
          </button>
        </div>

        {/* === PANEL 5: System Status (Bottom Center) === */}
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">System Status</h3>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            ✅ AI Model: Active
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            📶 Connection: Stable
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            💾 Storage: 42% Used
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            ⚙️ Resolution: 1080p
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            🕒 Uptime: 7h 24m
          </button>
        </div>

        {/* === PANEL 6: Settings & Export (Bottom Right) === */}
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">Actions</h3>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            📷 Capture Snapshot
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            📄 Generate Report
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            🔔 Set Alerts
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            📂 Save Session
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            🔐 Lock System
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;