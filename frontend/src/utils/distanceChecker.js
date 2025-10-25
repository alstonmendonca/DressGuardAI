/**
 * Distance/Full Body Checker
 * Validates if person is at appropriate distance before sending frame for detection
 * Uses simple image analysis to check if full outfit is visible
 */

/**
 * Check if the person is at an appropriate distance for full outfit detection
 * @param {HTMLVideoElement} video - The video element
 * @param {HTMLCanvasElement} canvas - Canvas for image processing
 * @returns {Object} - { isGoodDistance: boolean, message: string, confidence: number }
 */
export const checkDistance = (video, canvas) => {
  if (!video || !canvas) {
    return { isGoodDistance: false, message: "Camera not ready", confidence: 0 };
  }

  const ctx = canvas.getContext('2d');
  
  // Set canvas size to match video
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  
  // Draw current frame
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  // Get image data
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  
  // Analyze frame to estimate if full body is visible
  const analysis = analyzeFrame(data, canvas.width, canvas.height);
  
  let isGoodDistance = false;
  let message = "";
  let confidence = 0;
  
  if (analysis.faceDetected && analysis.facePosition === "top") {
    if (analysis.bodyFillRatio > 0.15 && analysis.bodyFillRatio < 0.70) {
      // Good distance - person is visible but not too close
      isGoodDistance = true;
      message = "Perfect! Full outfit visible";
      confidence = Math.min(95, 60 + (analysis.bodyFillRatio * 50));
    } else if (analysis.bodyFillRatio >= 0.70) {
      // Too close
      isGoodDistance = false;
      message = "⚠️ Step back - Too close to camera";
      confidence = 30;
    } else {
      // Too far
      isGoodDistance = false;
      message = "⚠️ Move closer - Too far from camera";
      confidence = 40;
    }
  } else if (analysis.faceDetected && analysis.facePosition === "middle") {
    isGoodDistance = false;
    message = "⚠️ Step back to show full outfit";
    confidence = 35;
  } else {
    // No clear face/body detected
    isGoodDistance = false;
    message = "⚠️ Position yourself in frame";
    confidence = 20;
  }
  
  return {
    isGoodDistance,
    message,
    confidence: Math.round(confidence),
    details: analysis
  };
};

/**
 * Analyze frame to detect body position and size
 * @param {Uint8ClampedArray} data - Image pixel data
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @returns {Object} - Analysis results
 */
function analyzeFrame(data, width, height) {
  // Divide frame into regions
  const topThird = Math.floor(height / 3);
  const middleThird = Math.floor(height * 2 / 3);
  
  let topRegionActivity = 0;
  let middleRegionActivity = 0;
  let bottomRegionActivity = 0;
  let totalActivity = 0;
  
  // Sample pixels (every 10th pixel for performance)
  const step = 10;
  let sampledPixels = 0;
  
  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      const i = (y * width + x) * 4;
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      
      // Calculate activity (edge detection approximation)
      // Look for color variation indicating a person
      const activity = Math.abs(r - g) + Math.abs(g - b) + Math.abs(b - r);
      
      if (y < topThird) {
        topRegionActivity += activity;
      } else if (y < middleThird) {
        middleRegionActivity += activity;
      } else {
        bottomRegionActivity += activity;
      }
      
      totalActivity += activity;
      sampledPixels++;
    }
  }
  
  // Normalize activity levels
  const avgActivity = totalActivity / sampledPixels;
  const topRatio = topRegionActivity / (sampledPixels / 3);
  const middleRatio = middleRegionActivity / (sampledPixels / 3);
  const bottomRatio = bottomRegionActivity / (sampledPixels / 3);
  
  // Detect where the most activity is (likely where person is)
  let faceDetected = topRatio > avgActivity * 0.8;
  let facePosition = "none";
  
  if (topRatio > middleRatio && topRatio > bottomRatio && topRatio > avgActivity * 0.7) {
    facePosition = "top";
    faceDetected = true;
  } else if (middleRatio > topRatio && middleRatio > avgActivity * 0.7) {
    facePosition = "middle";
    faceDetected = true;
  }
  
  // Estimate body fill ratio (how much of frame is filled)
  const bodyFillRatio = totalActivity / (sampledPixels * 255 * 3);
  
  return {
    faceDetected,
    facePosition,
    bodyFillRatio,
    topActivity: topRatio / avgActivity,
    middleActivity: middleRatio / avgActivity,
    bottomActivity: bottomRatio / avgActivity
  };
}

/**
 * Simple distance check based on video dimensions and heuristics
 * Fallback method when canvas analysis is not needed
 * @param {HTMLVideoElement} video 
 * @returns {Object}
 */
export const quickDistanceCheck = (video) => {
  if (!video || !video.videoWidth) {
    return { isGoodDistance: false, message: "Camera initializing...", confidence: 0 };
  }
  
  // For now, allow processing after initial check
  // This is a placeholder for more sophisticated checks
  return { 
    isGoodDistance: true, 
    message: "Ready to detect", 
    confidence: 80 
  };
};

/**
 * Check if enough time has passed since last frame
 * Implements throttling to reduce backend stress
 * @param {number} lastCheckTime - Timestamp of last check
 * @param {number} intervalMs - Minimum interval between checks (default 2000ms)
 * @returns {boolean}
 */
export const shouldCheckFrame = (lastCheckTime, intervalMs = 2000) => {
  const now = Date.now();
  return (now - lastCheckTime) >= intervalMs;
};
