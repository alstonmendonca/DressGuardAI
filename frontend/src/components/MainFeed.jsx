// components/MainFeed.jsx
import React from "react";

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
  startWebcam,
}) {
  return (
    <div className="col-span-2 row-span-1 relative border-4 border-green-500 shadow-lg rounded overflow-hidden">
      {activeFeed === "image" && imageURL ? (
        <>
          <img
            src={imageURL}
            alt="Uploaded"
            ref={imageRef}
            onLoad={() =>
              detections.length > 0 &&
              drawBoxes({
                canvasRef,
                imageRef,
                videoRef,
                activeFeed,
                detections
              })
            }
            className="w-full h-auto"
          />
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 pointer-events-none"
          />
        </>
      ) : activeFeed === "video" && imageURL ? (
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
                  detections
                });
              });
            }}
            onEnded={() => (isDetecting.current = false)}
            playsInline
            autoPlay
          />
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 pointer-events-none"
          />
        </>
      ) : activeFeed === "webcam" ? (
        // ✅ Show "Turn on Webcam" button
        videoRef.current?.srcObject ? (
          // If stream is active, show video + canvas
          <>
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="w-full h-auto"
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none"
            />
          </>
        ) : (
          // If not, show button
          <div className="w-full h-64 bg-black flex flex-col items-center justify-center space-y-4">
            <span className="text-green-600">Webcam is off</span>
            <button
              className="bg-green-700 hover:bg-green-600 text-black px-6 py-2 rounded font-mono text-sm"
              onClick={startWebcam}
            >
              Turn on Webcam
            </button>
          </div>
        )
      ) : (
        <div className="w-full h-64 bg-black flex items-center justify-center">
          <span className="text-green-600">Upload an image or video</span>
        </div>
      )}
    </div>
  );
}
