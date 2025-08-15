export default function detectFrameFromVideo({ 
  imageRef,videoRef, activeFeed, canvasRef, isDetecting, setDetections, drawBoxes, detections 
}) {
    if (isDetecting.current) return;
    isDetecting.current = true;

    const video = videoRef.current;
    const displayCanvas = canvasRef.current; // For drawing boxes only
    if (!video || !displayCanvas) {
        isDetecting.current = false;
        return;
    }

    // ✅ Step 1: Use a temporary canvas to extract the frame for detection
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    tempCtx.drawImage(video, 0, 0);

    // ✅ Step 2: Send frame to backend
    tempCanvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
        const response = await fetch("http://127.0.0.1:8000/detect/", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            setDetections(data.clothes_detected);
            requestAnimationFrame(() => 
            drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })    // Ensure DOM is ready
            );
            

            // ✅ Step 3: Only draw boxes — no video redraw
            drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections });
        }
        } catch (err) {
        console.error("Detection error:", err);
        } finally {
        isDetecting.current = false;
        }
    }, "image/jpeg", 0.7);
  
}
