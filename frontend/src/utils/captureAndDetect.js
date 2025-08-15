// export default function captureAndDetect({ 
//   videoRef, canvasRef, isDetecting, setDetections, drawBoxes 
// }) {
//     const video = videoRef.current;
//     const canvas = canvasRef.current;

//     if (!video || !canvas || isDetecting.current) {
//         requestAnimationFrame(captureAndDetect);
//         return;
//     }

//     isDetecting.current = true;

//     // Draw current frame to canvas
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     canvas.getContext("2d").drawImage(video, 0, 0);

//     // Convert to blob and send
//     canvas.toBlob(async (blob) => {
//         const formData = new FormData();
//         formData.append("file", blob, "frame.jpg");

//         try {
//         const response = await fetch("http://127.0.0.1:8000/detect/", {
//             method: "POST",
//             body: formData,
//         });

//         if (response.ok) {
//             const data = await response.json();
//             setDetections(data.clothes_detected);
//             drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections });
//         }
//         } catch (err) {
//         console.error("Detection error:", err);
//         } finally {
//         isDetecting.current = false;
//         }
//     }, "image/jpeg", 0.7);

//     requestAnimationFrame(captureAndDetect); // Continue loop
  
// }
