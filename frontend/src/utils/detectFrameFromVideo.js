import { logComplianceResults } from './complianceLogger';

/**
 * Enhanced frame detection with better performance and error handling
 * Features:
 * - Optimized canvas reuse
 * - Better error handling and recovery
 * - Configurable quality and confidence thresholds
 * - Request timeout and abort handling
 */

// Configuration
const JPEG_QUALITY = 0.75;  // Balance between quality and speed
const CONFIDENCE_THRESHOLD = 0.6;  // Minimum confidence for detections
const REQUEST_TIMEOUT = 5000;  // 5 seconds timeout for API requests
const MAX_RETRIES = 2;  // Maximum number of retries on failure

// Reusable canvas for better performance (avoid creating new canvas each time)
let sharedCanvas = null;
let sharedContext = null;

function getSharedCanvas(width, height) {
  if (!sharedCanvas) {
    sharedCanvas = document.createElement('canvas');
    sharedContext = sharedCanvas.getContext('2d', { alpha: false });
  }
  
  if (sharedCanvas.width !== width || sharedCanvas.height !== height) {
    sharedCanvas.width = width;
    sharedCanvas.height = height;
  }
  
  return { canvas: sharedCanvas, ctx: sharedContext };
}

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
  retryCount = 0
}) {
  // Prevent concurrent detections
  if (isDetecting.current) return;
  isDetecting.current = true;

  const video = videoRef.current;
  const displayCanvas = canvasRef.current;

  // Validation
  if (!video || !displayCanvas) {
    console.warn("Video or canvas not available");
    isDetecting.current = false;
    return;
  }

  // Check video readiness
  if (video.videoWidth === 0 || video.videoHeight === 0 || video.readyState < 2) {
    console.debug("Video not ready for frame capture");
    isDetecting.current = false;
    return;
  }

  // Get or create shared canvas for performance
  const { canvas: tempCanvas, ctx: tempCtx } = getSharedCanvas(
    video.videoWidth,
    video.videoHeight
  );

  try {
    // Clear previous frame
    tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
    
    // Draw current video frame
    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
  } catch (err) {
    console.error("Failed to draw video frame:", err);
    isDetecting.current = false;
    return;
  }

  // Convert to blob with optimized quality
  tempCanvas.toBlob(
    async (blob) => {
      if (!blob) {
        console.warn("Canvas.toBlob() returned null. Frame skipped.");
        isDetecting.current = false;
        return;
      }

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");
      formData.append("model", currentModel);

      try {
        const response = await fetch("/api/detect/", {
          method: "POST",
          body: formData,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Detection failed (${response.status}):`, errorText);
          
          // Retry on server errors if retries available
          if (response.status >= 500 && retryCount < MAX_RETRIES) {
            console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
            isDetecting.current = false;
            setTimeout(() => {
              detectFrameFromVideo({
                imageRef, videoRef, activeFeed, canvasRef,
                isDetecting, setDetections, drawBoxes, detections,
                currentModel, retryCount: retryCount + 1
              });
            }, 1000);
            return;
          }
          
          isDetecting.current = false;
          return;
        }

        const data = await response.json();
        
        // Filter detections by confidence threshold
        const filteredDetections = data.clothes_detected.filter(
          det => det.confidence >= CONFIDENCE_THRESHOLD
        );
        
        // Update detections
        setDetections(filteredDetections);
        
        // Log compliance (throttled in parent component)
        logComplianceResults(data, "Video Frame");

        // Draw boxes on next animation frame for smooth rendering
        requestAnimationFrame(() => {
          drawBoxes({
            canvasRef,
            imageRef,
            videoRef,
            activeFeed,
            detections: filteredDetections
          });
        });

      } catch (err) {
        clearTimeout(timeoutId);
        
        if (err.name === 'AbortError') {
          console.warn("Detection request timeout - frame skipped");
        } else {
          console.error("Fetch error:", err.message);
        }
        
        // Retry on network errors if retries available
        if (retryCount < MAX_RETRIES && err.name !== 'AbortError') {
          console.log(`Retrying after error... (${retryCount + 1}/${MAX_RETRIES})`);
          isDetecting.current = false;
          setTimeout(() => {
            detectFrameFromVideo({
              imageRef, videoRef, activeFeed, canvasRef,
              isDetecting, setDetections, drawBoxes, detections,
              currentModel, retryCount: retryCount + 1
            });
          }, 1000);
          return;
        }
      } finally {
        isDetecting.current = false;
      }
    },
    "image/jpeg",
    JPEG_QUALITY
  );
}

// Cleanup function to release shared canvas when done
export function cleanupSharedCanvas() {
  if (sharedCanvas) {
    sharedCanvas.width = 0;
    sharedCanvas.height = 0;
    sharedCanvas = null;
    sharedContext = null;
  }
}