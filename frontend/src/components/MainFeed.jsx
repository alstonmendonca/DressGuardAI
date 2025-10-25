// src/components/MainFeed.jsx
import React, { useEffect, useState } from "react";

export default function MainFeed({
  activeFeed,
  imageURL,
  imageRef,
  videoRef,
  canvasRef,
  hiddenCanvasRef,
  detections,
  drawBoxes,
  detectFrameFromVideo,
  isDetecting,
  setDetections,
  setupWebcamStream,   
  onWebcamStreamStart,
  currentModel, // Add currentModel to props
}) {
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (activeFeed === "webcam" && videoRef.current) {
      console.log("🔹 Video element is mounted, calling setupWebcamStream");
      setupWebcamStream(); // now videoRef.current is NOT null
    }
  }, [activeFeed, videoRef, setupWebcamStream]);

  return (
    <div className="col-span-2 row-span-1 relative border-4 border-green-500 shadow-lg rounded overflow-hidden">
      {/* --- IMAGE MODE --- */}
      {activeFeed === "image" && imageURL ? (
        <>
          <img
            src={imageURL}
            alt="Uploaded"
            ref={imageRef}
            onLoad={() =>
              detections.length > 0 &&
              drawBoxes({ canvasRef, imageRef, videoRef, activeFeed, detections })
            }
            className="w-full h-auto"
          />
          <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
        </>
      ) : /* --- VIDEO MODE --- */ activeFeed === "video" && imageURL ? (
        <>
          <video
            ref={videoRef}
            src={imageURL}
            className="w-full h-auto"
            onLoadedMetadata={(e) => {
              e.target.play();
              e.target.addEventListener("timeupdate", () => {
                detectFrameFromVideo({
                  imageRef,
                  videoRef,
                  activeFeed,
                  canvasRef,
                  isDetecting,
                  setDetections,
                  drawBoxes,
                  detections,
                  currentModel, // Add currentModel to props
                });
              });
            }}
            onEnded={() => (isDetecting.current = false)}
            playsInline
            autoPlay
          />
          <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
        </>
      ) : /* --- WEBCAM MODE (Backend MJPEG Stream) --- */ activeFeed === "webcam" ? (
        <>
          <img
            src="/api/webcam/stream/"
            alt="Live Webcam Detection"
            className="w-full h-auto"
            onLoad={() => {
              console.log("Webcam stream started");
              setIsStreaming(true);
              onWebcamStreamStart();
            }}
            onError={(e) => {
              console.error("Webcam stream error:", e);
              setIsStreaming(false);
            }}
          />
          {/* No canvas needed - backend handles annotations */}
        </>
      ) : (
        <div className="w-full h-64 bg-black flex items-center justify-center">
          <span className="text-green-600">Upload an image or video</span>
        </div>
      )}
    </div>
  );
}