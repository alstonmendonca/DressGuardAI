// src/components/MainFeed.jsx
import React, { useEffect, useState } from "react";

export default function MainFeed({
  activeFeed,
  imageURL,
  imageRef,
  videoRef,
  canvasRef,
  detections,
  drawBoxes,
  detectFrameFromVideo,
  isDetecting,
  setDetections,
  setupWebcamStream,   // 👈 pass this from App.jsx
  onWebcamStreamStart,
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
                });
              });
            }}
            onEnded={() => (isDetecting.current = false)}
            playsInline
            autoPlay
          />
          <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
        </>
      ) : /* --- WEBCAM MODE --- */ activeFeed === "webcam" ? (
        <>
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="w-full h-auto"
            onPlay={() => {
              console.log("▶️ Webcam started playing");
              setIsStreaming(true);
              onWebcamStreamStart();
            }}
          />
          <canvas ref={canvasRef} className="absolute top-0 left-0 pointer-events-none" />
        </>
      ) : (
        <div className="w-full h-64 bg-black flex items-center justify-center">
          <span className="text-green-600">Upload an image or video</span>
        </div>
      )}
    </div>
  );
}