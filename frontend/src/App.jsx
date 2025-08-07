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
    setImageURL(imageBlobURL); // Show the image

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

    canvas.width = img.width;
    canvas.height = img.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set box style
    ctx.lineWidth = 2;
    ctx.font = "16px sans-serif";
    ctx.strokeStyle = "red";
    ctx.fillStyle = "red";

    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.fillText(`${det.class} (${Math.round(det.confidence * 100)}%)`, x1, y1 - 5);
    });
  };

  return (
    <div className="p-4 max-w-3xl mx-auto text-center">
      <h1 className="text-2xl font-bold mb-4">DressGuard AI Detection</h1>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="mb-4"
      />
      <div className="relative inline-block">
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
              className="absolute top-0 left-0"
              style={{ pointerEvents: 'none' }}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
