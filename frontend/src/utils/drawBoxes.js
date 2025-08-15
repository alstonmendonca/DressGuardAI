// src/utils/drawBoxes.js
/**
 * Draws bounding boxes and labels on the canvas based on detection results.
 * Scales coordinates from original image dimensions to displayed size.
 * Also draws a crosshair at the center (UI sniper-scope effect).
 */

export default function drawBoxes({ 
  canvasRef, imageRef, videoRef, activeFeed, detections 
}) {
  const canvas = canvasRef.current;
  const ctx = canvas?.getContext("2d");
  let img;

  if (activeFeed === 'video') {
    img = videoRef.current;
  } else if (activeFeed === 'image') {
    img = imageRef.current;
  } else {
    return;
  }

  if (!canvas || !ctx || !img) {
    console.warn("Missing canvas, ctx, or img");
    return;
  }

  // ✅ Use rendered size (what's on screen)
  const displayWidth = img.clientWidth || img.width || 640;
  const displayHeight = img.clientHeight || img.height || 480;

  // Ensure canvas matches rendered size
  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }

  // Clear previous drawings
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Set styles
  ctx.lineWidth = 2;
  ctx.font = "16px monospace";
  ctx.strokeStyle = "#00FF00";
  ctx.fillStyle = "#00FF00";

  // Scaling from original → displayed
  const originalWidth = img.naturalWidth || img.videoWidth;
  const originalHeight = img.naturalHeight || img.videoHeight;
  const scaleX = displayWidth / originalWidth;
  const scaleY = displayHeight / originalHeight;

  detections.forEach((det) => {
    const [x1, y1, x2, y2] = det.bbox;

    // Scale to rendered size
    const sx1 = x1 * scaleX;
    const sy1 = y1 * scaleY;
    const width = (x2 - x1) * scaleX;
    const height = (y2 - y1) * scaleY;

    // Safety: skip if out of bounds
    if (isNaN(sx1) || isNaN(sy1) || isNaN(width) || isNaN(height)) return;

    ctx.strokeRect(sx1, sy1, width, height);

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
}
