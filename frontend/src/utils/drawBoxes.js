// src/utils/drawBoxes.js
/**
 * Draws bounding boxes and labels on the canvas based on detection results.
 * Scales coordinates from original image dimensions to displayed size.
 * Also draws a crosshair at the center (UI sniper-scope effect).
 */

export default function drawBoxes({ 
  canvasRef, 
  imageRef, 
  videoRef, 
  activeFeed, 
  detections 
}) {
  const canvas = canvasRef.current;
  const ctx = canvas?.getContext("2d");

  let img;
  if (activeFeed === 'image') {
    img = imageRef.current;
  } else if (activeFeed === 'video' || activeFeed === 'webcam') {
    img = videoRef.current;
  } else {
    return;
  }

  if (!canvas || !ctx || !img) {
    // Don't warn every frame — only once
    return;
  }

  console.log("drawBoxes called:", { activeFeed, detections: detections.length, canvas: !!canvas, img: !!img });

  const displayWidth = img.clientWidth || img.width || 640;
  const displayHeight = img.clientHeight || img.height || 480;

  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 2;
  ctx.font = "16px monospace";
  ctx.strokeStyle = "#00FF00";
  ctx.fillStyle = "#00FF00";

  const originalWidth = img.naturalWidth || img.videoWidth;
  const originalHeight = img.naturalHeight || img.videoHeight;
  const scaleX = displayWidth / originalWidth;
  const scaleY = displayHeight / originalHeight;

  detections.forEach((det) => {
    const [x1, y1, x2, y2] = det.bbox;
    const sx1 = x1 * scaleX;
    const sy1 = y1 * scaleY;
    const width = (x2 - x1) * scaleX;
    const height = (y2 - y1) * scaleY;

    if (isNaN(sx1) || isNaN(sy1)) return;

    ctx.strokeRect(sx1, sy1, width, height);
    ctx.fillText(
      `${det.class} (${Math.round(det.confidence * 100)}%)`,
      sx1,
      sy1 > 20 ? sy1 - 5 : sy1 + 20
    );
  });

  // Crosshair
  ctx.strokeStyle = "#00FF00";
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2 - 20, canvas.height / 2);
  ctx.lineTo(canvas.width / 2 + 20, canvas.height / 2);
  ctx.moveTo(canvas.width / 2, canvas.height / 2 - 20);
  ctx.lineTo(canvas.width / 2, canvas.height / 2 + 20);
  ctx.stroke();
}