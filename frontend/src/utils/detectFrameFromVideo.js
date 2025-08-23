import { logComplianceResults } from './complianceLogger';

export default function detectFrameFromVideo({
  imageRef,
  videoRef,
  activeFeed,
  canvasRef,
  isDetecting,
  setDetections,
  drawBoxes,
  detections,
  currentModel, 
}) {
  if (isDetecting.current) return;
  isDetecting.current = true;

  const video = videoRef.current;
  if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
    isDetecting.current = false;
    return;
    }
  
  const displayCanvas = canvasRef.current;

  if (!video || !displayCanvas) {
    isDetecting.current = false;
    return;
  }

  // Create temporary canvas to extract frame
  const tempCanvas = document.createElement('canvas');
  const tempCtx = tempCanvas.getContext('2d');
  tempCanvas.width = video.videoWidth;
  tempCanvas.height = video.videoHeight;

  try {
    // Draw current video frame
    tempCtx.drawImage(video, 0, 0);
  } catch (err) {
    console.error("Failed to draw video frame:", err);
    isDetecting.current = false;
    return;
  }

  // Convert to blob
  tempCanvas.toBlob(
    async (blob) => {
      // ✅ CHECK IF BLOB IS NULL
      if (!blob) {
        console.warn("Canvas.toBlob() returned null. Frame skipped.");
        isDetecting.current = false;
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "frame.jpg"); // ✅ Now safe
      formData.append("model", currentModel); // Add current model to request

      try {
        const response = await fetch("/api/detect/", {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          setDetections(data.clothes_detected);
          logComplianceResults(data, "Video Frame");

          // Draw boxes after detection
          requestAnimationFrame(() => {
            drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections });
          });
        } else {
          console.error("Detection failed:", await response.text());
        }
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        isDetecting.current = false; // Unlock for next frame
      }
    },
    "image/jpeg",
    0.7
  );
}