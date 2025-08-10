import { useState, useRef, useEffect } from 'react';  // ← useEffect added!
import './App.css';

function App() {
  const [imageURL, setImageURL] = useState(null);
  const [detections, setDetections] = useState([]);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  // This function must be stable or re-created safely
  const drawBoxes = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = imageRef.current;

    if (!canvas || !ctx || !img) {
      console.warn("Missing canvas, context, or image");
      return;
    }

    // Use actual rendered size (after browser scales)
    const displayWidth = img.width;
    const displayHeight = img.height;

    // Set canvas to match rendered image size
    canvas.width = displayWidth;
    canvas.height = displayHeight;

    // Scale from original to displayed
    const scaleX = displayWidth / img.naturalWidth;
    const scaleY = displayHeight / img.naturalHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2;
    ctx.font = "16px monospace";
    ctx.strokeStyle = "#00FF00";
    ctx.fillStyle = "#00FF00";

    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;

      const sx1 = x1 * scaleX;
      const sy1 = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      ctx.strokeRect(sx1, sy1, width, height);

      // Text above box, but not outside image
      const textY = sy1 > 20 ? sy1 - 5 : sy1 + 20;
      ctx.fillText(`${det.class} (${Math.round(det.confidence * 100)}%)`, sx1, textY);
    });

    // Draw crosshair
    ctx.strokeStyle = "#00FF00";
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2 - 20, canvas.height / 2);
    ctx.lineTo(canvas.width / 2 + 20, canvas.height / 2);
    ctx.moveTo(canvas.width / 2, canvas.height / 2 - 20);
    ctx.lineTo(canvas.width / 2, canvas.height / 2 + 20);
    ctx.stroke();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const imageBlobURL = URL.createObjectURL(file);
    setImageURL(imageBlobURL);
    setDetections([]); // reset previous detections

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/detect/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        console.error("Detection failed:", await response.text());
        return;
      }

      const data = await response.json();
      console.log("Detection result:", data);
      setDetections(data.clothes_detected);

      // If image is already loaded, draw now
      if (imageRef.current?.complete) {
        console.log("Image already loaded, drawing boxes...");
        drawBoxes();
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  // Optional: Redraw if detections or image changes
  useEffect(() => {
    if (imageURL && detections.length > 0 && imageRef.current?.complete) {
      console.log("Redrawing boxes (useEffect)");
      drawBoxes();
    }
  }, [imageURL, detections]);

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono flex flex-col items-center p-6">
      <h1 className="text-3xl mb-6 border-b-2 pb-2 border-green-400 tracking-widest uppercase">
        DressGuard AI - Surveillance Mode
      </h1>

      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="mb-6 bg-green-900 text-green-300 border border-green-400 p-2 rounded hover:bg-green-800 transition-all"
      />

      <div className="relative border-4 border-green-500 shadow-lg rounded overflow-hidden">
        {imageURL && (
          <>
            <img
              src={imageURL}
              alt="Uploaded"
              ref={imageRef}
              onLoad={() => {
                console.log("Image loaded, calling drawBoxes");
                if (detections.length > 0) drawBoxes();
              }}
              className="max-w-full"
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none"
            />
          </>
        )}
      </div>

      {detections.length > 0 && (
        <div className="mt-6 bg-green-950 p-4 rounded shadow-lg max-w-xl w-full text-left">
          <h2 className="text-xl mb-2 border-b border-green-400">Detected Items:</h2>
          <ul className="list-disc pl-6">
            {detections.map((det, index) => (
              <li key={index}>
                <span className="font-bold">{det.class}</span> —{" "}
                {(det.confidence * 100).toFixed(2)}% confidence
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;