// src/utils/drawBoxes.js
/**
 * Enhanced bounding box drawing with better performance and visual improvements
 * Features:
 * - Optimized rendering with batch operations
 * - Configurable styling and thresholds
 * - Better text rendering with background
 * - Performance optimizations
 */

// Configuration
const CONFIDENCE_THRESHOLD = 0.6;  // Minimum confidence to display
const BOX_COLOR = '#00FF00';        // Green for compliant
const WARNING_COLOR = '#FFA500';    // Orange for low confidence
const DANGER_COLOR = '#FF0000';     // Red for non-compliant
const FONT_SIZE = 14;
const FONT_FAMILY = 'monospace';
const LINE_WIDTH = 2;
const TEXT_PADDING = 4;
const CROSSHAIR_SIZE = 20;

/**
 * Draws bounding boxes and labels on the canvas based on detection results.
 * Scales coordinates from original image dimensions to displayed size.
 */
export default function drawBoxes({ 
  canvasRef, 
  imageRef, 
  videoRef, 
  activeFeed, 
  detections 
}) {
  const canvas = canvasRef.current;
  const ctx = canvas?.getContext('2d');

  // Determine source element based on active feed
  let sourceElement;
  if (activeFeed === 'image') {
    sourceElement = imageRef.current;
  } else if (activeFeed === 'video' || activeFeed === 'webcam' || activeFeed === 'ipcam') {
    sourceElement = videoRef.current;
  }

  // Validation
  if (!canvas || !ctx || !sourceElement) {
    return;
  }

  // Get display dimensions
  const displayWidth = sourceElement.clientWidth || sourceElement.width || 640;
  const displayHeight = sourceElement.clientHeight || sourceElement.height || 480;

  // Only resize canvas if dimensions actually changed (prevents flicker)
  const needsResize = canvas.width !== displayWidth || canvas.height !== displayHeight;
  if (needsResize) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }

  // Clear canvas (using willReadFrequently optimized context)
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Get original dimensions for scaling
  const originalWidth = sourceElement.naturalWidth || sourceElement.videoWidth || displayWidth;
  const originalHeight = sourceElement.naturalHeight || sourceElement.videoHeight || displayHeight;
  
  // Calculate scale factors
  const scaleX = displayWidth / originalWidth;
  const scaleY = displayHeight / originalHeight;

  // Filter detections by confidence threshold
  const filteredDetections = (detections || []).filter(
    det => det.confidence >= CONFIDENCE_THRESHOLD
  );

  if (filteredDetections.length === 0) {
    // Draw crosshair even if no detections
    drawCrosshair(ctx, canvas.width, canvas.height);
    return;
  }

  // Set default text style
  ctx.font = `${FONT_SIZE}px ${FONT_FAMILY}`;
  ctx.lineWidth = LINE_WIDTH;

  // Draw all boxes
  filteredDetections.forEach((det) => {
    const [x1, y1, x2, y2] = det.bbox;
    
    // Scale coordinates
    const sx1 = x1 * scaleX;
    const sy1 = y1 * scaleY;
    const width = (x2 - x1) * scaleX;
    const height = (y2 - y1) * scaleY;

    // Validation
    if (isNaN(sx1) || isNaN(sy1) || width <= 0 || height <= 0) {
      return;
    }

    // Determine color based on confidence
    const color = getColorForConfidence(det.confidence);
    
    // Draw bounding box
    ctx.strokeStyle = color;
    ctx.strokeRect(sx1, sy1, width, height);

    // Draw corner markers for better visibility
    drawCornerMarkers(ctx, sx1, sy1, width, height, color);

    // Prepare label text
    const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
    const textMetrics = ctx.measureText(label);
    const textWidth = textMetrics.width;
    const textHeight = FONT_SIZE;

    // Calculate label position (above box if space, otherwise inside)
    const labelX = sx1;
    const labelY = sy1 > textHeight + TEXT_PADDING * 2 ? sy1 - TEXT_PADDING : sy1 + textHeight + TEXT_PADDING;

    // Draw label background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(
      labelX,
      labelY - textHeight - TEXT_PADDING,
      textWidth + TEXT_PADDING * 2,
      textHeight + TEXT_PADDING * 2
    );

    // Draw label text
    ctx.fillStyle = color;
    ctx.fillText(label, labelX + TEXT_PADDING, labelY - TEXT_PADDING);
  });

  // Draw crosshair
  drawCrosshair(ctx, canvas.width, canvas.height);
}

/**
 * Get color based on confidence level
 */
function getColorForConfidence(confidence) {
  if (confidence >= 0.8) {
    return BOX_COLOR;  // High confidence - green
  } else if (confidence >= 0.7) {
    return WARNING_COLOR;  // Medium confidence - orange
  } else {
    return WARNING_COLOR;  // Low confidence - orange
  }
}

/**
 * Draw corner markers for better box visibility
 */
function drawCornerMarkers(ctx, x, y, width, height, color) {
  const markerLength = Math.min(15, width / 4, height / 4);
  
  ctx.strokeStyle = color;
  ctx.lineWidth = LINE_WIDTH + 1;
  
  // Top-left
  ctx.beginPath();
  ctx.moveTo(x, y + markerLength);
  ctx.lineTo(x, y);
  ctx.lineTo(x + markerLength, y);
  ctx.stroke();
  
  // Top-right
  ctx.beginPath();
  ctx.moveTo(x + width - markerLength, y);
  ctx.lineTo(x + width, y);
  ctx.lineTo(x + width, y + markerLength);
  ctx.stroke();
  
  // Bottom-left
  ctx.beginPath();
  ctx.moveTo(x, y + height - markerLength);
  ctx.lineTo(x, y + height);
  ctx.lineTo(x + markerLength, y + height);
  ctx.stroke();
  
  // Bottom-right
  ctx.beginPath();
  ctx.moveTo(x + width - markerLength, y + height);
  ctx.lineTo(x + width, y + height);
  ctx.lineTo(x + width, y + height - markerLength);
  ctx.stroke();
  
  ctx.lineWidth = LINE_WIDTH;  // Reset line width
}

/**
 * Draw center crosshair
 */
function drawCrosshair(ctx, width, height) {
  const centerX = width / 2;
  const centerY = height / 2;
  
  ctx.strokeStyle = BOX_COLOR;
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.5;
  
  ctx.beginPath();
  // Horizontal line
  ctx.moveTo(centerX - CROSSHAIR_SIZE, centerY);
  ctx.lineTo(centerX + CROSSHAIR_SIZE, centerY);
  // Vertical line
  ctx.moveTo(centerX, centerY - CROSSHAIR_SIZE);
  ctx.lineTo(centerX, centerY + CROSSHAIR_SIZE);
  ctx.stroke();
  
  // Center dot
  ctx.fillStyle = BOX_COLOR;
  ctx.beginPath();
  ctx.arc(centerX, centerY, 2, 0, Math.PI * 2);
  ctx.fill();
  
  ctx.globalAlpha = 1.0;  // Reset alpha
}