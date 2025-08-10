import { useState, useRef } from 'react';
import './App.css';

function App() {
  const [imageURL, setImageURL] = useState(null);
  const [detections, setDetections] = useState([]);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const imageBlobURL = URL.createObjectURL(file);
    setImageURL(imageBlobURL);

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://127.0.0.1:8000/detect/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    setDetections(data.clothes_detected);
  };

  const drawBoxes = () => {
  const canvas = canvasRef.current;
  const ctx = canvas.getContext("2d");
  const img = imageRef.current;

  if (!canvas || !ctx || !img) return;

  // Get actual displayed size
  const displayWidth = img.clientWidth;
  const displayHeight = img.clientHeight;
  canvas.width = displayWidth;
  canvas.height = displayHeight;

  // Scale factors from original image → displayed size
  const scaleX = displayWidth / img.naturalWidth;
  const scaleY = displayHeight / img.naturalHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.lineWidth = 2;
  ctx.font = "16px monospace";
  ctx.strokeStyle = "#00FF00";
  ctx.fillStyle = "#00FF00";

  detections.forEach((det) => {
    const [x1, y1, x2, y2] = det.bbox;

    // Scale only if needed
    const sx1 = x1 * scaleX;
    const sy1 = y1 * scaleY;
    const sx2 = x2 * scaleX;
    const sy2 = y2 * scaleY;

    ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);
    ctx.fillText(
      `${det.class} (${Math.round(det.confidence * 100)}%)`,
      sx1,
      sy1 - 5
    );
  });

  // Sniper crosshair
  ctx.strokeStyle = "#00FF00";
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2 - 20, canvas.height / 2);
  ctx.lineTo(canvas.width / 2 + 20, canvas.height / 2);
  ctx.moveTo(canvas.width / 2, canvas.height / 2 - 20);
  ctx.lineTo(canvas.width / 2, canvas.height / 2 + 20);
  ctx.stroke();
};



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
              onLoad={drawBoxes}
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
          <h2 className="text-xl mb-2 border-b border-green-400 rounded-2xl">Detected Items:</h2>
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
