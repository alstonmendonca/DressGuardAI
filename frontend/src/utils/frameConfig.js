/**
 * Frame Processing Configuration
 * Centralized settings for video/webcam detection
 */

export const FRAME_CONFIG = {
  // Detection settings
  CONFIDENCE_THRESHOLD: 0.6,        // Minimum confidence to display (0-1)
  DETECTION_INTERVAL_MS: 150,       // Smart throttling: ~6-7 FPS for stable real-time detection
  STATE_UPDATE_INTERVAL_MS: 0,      // Update state immediately
  LOG_INTERVAL_MS: 3000,            // How often to log compliance (milliseconds)
  
  // Quality settings
  JPEG_QUALITY: 0.75,               // JPEG compression quality (0-1)
  MAX_FRAME_WIDTH: 1280,            // Max width for frame processing
  MAX_FRAME_HEIGHT: 720,            // Max height for frame processing
  
  // Network settings
  REQUEST_TIMEOUT_MS: 5000,         // API request timeout (milliseconds)
  MAX_RETRIES: 2,                   // Maximum retry attempts on failure
  RETRY_DELAY_MS: 1000,             // Delay between retries (milliseconds)
  
  // Performance settings
  USE_SHARED_CANVAS: true,          // Reuse canvas for better performance
  USE_REQUEST_ANIMATION_FRAME: true,// Use RAF for smooth rendering
  ADAPTIVE_QUALITY: false,          // Adjust quality based on performance (future)
  REAL_TIME_MODE: true,             // Enable optimized real-time detection
  PREVENT_CANVAS_FLICKER: true,     // Only resize canvas when dimensions change
  
  // Visual settings
  DRAW_CROSSHAIR: true,             // Show center crosshair
  DRAW_CORNER_MARKERS: true,        // Show corner markers on boxes
  TEXT_BACKGROUND: true,            // Show background behind labels
  COLOR_BY_CONFIDENCE: true,        // Use different colors for confidence levels
  
  // Colors
  COLORS: {
    HIGH_CONFIDENCE: '#00FF00',     // Green (>= 0.8)
    MEDIUM_CONFIDENCE: '#FFA500',   // Orange (0.7-0.8)
    LOW_CONFIDENCE: '#FFA500',      // Orange (< 0.7)
    CROSSHAIR: '#00FF00',           // Green
    TEXT_BACKGROUND: 'rgba(0, 0, 0, 0.7)'
  },
  
  // Font settings
  FONT: {
    SIZE: 14,
    FAMILY: 'monospace',
    LINE_WIDTH: 2,
    TEXT_PADDING: 4
  },
  
  // Debug settings
  DEBUG_MODE: false,                // Enable debug logging
  SHOW_PERFORMANCE_METRICS: false,  // Show performance overlay
  LOG_FRAME_SKIPS: false           // Log when frames are skipped
};

/**
 * Get optimized config for different scenarios
 */
export function getOptimizedConfig(scenario = 'default') {
  const configs = {
    // High quality, slower
    'high-quality': {
      ...FRAME_CONFIG,
      JPEG_QUALITY: 0.9,
      DETECTION_INTERVAL_MS: 200,
      CONFIDENCE_THRESHOLD: 0.7
    },
    
    // Balanced (default)
    'default': FRAME_CONFIG,
    
    // Fast, lower quality
    'performance': {
      ...FRAME_CONFIG,
      JPEG_QUALITY: 0.6,
      DETECTION_INTERVAL_MS: 50,
      CONFIDENCE_THRESHOLD: 0.5,
      MAX_FRAME_WIDTH: 640,
      MAX_FRAME_HEIGHT: 480
    },
    
    // For slow networks
    'low-bandwidth': {
      ...FRAME_CONFIG,
      JPEG_QUALITY: 0.5,
      DETECTION_INTERVAL_MS: 300,
      MAX_FRAME_WIDTH: 640,
      MAX_FRAME_HEIGHT: 480,
      REQUEST_TIMEOUT_MS: 10000
    }
  };
  
  return configs[scenario] || FRAME_CONFIG;
}

/**
 * Validate and adjust config values
 */
export function validateConfig(config) {
  const validated = { ...config };
  
  // Ensure values are in valid ranges
  validated.CONFIDENCE_THRESHOLD = Math.max(0, Math.min(1, config.CONFIDENCE_THRESHOLD));
  validated.JPEG_QUALITY = Math.max(0.1, Math.min(1, config.JPEG_QUALITY));
  validated.DETECTION_INTERVAL_MS = Math.max(0, config.DETECTION_INTERVAL_MS);
  validated.REQUEST_TIMEOUT_MS = Math.max(1000, config.REQUEST_TIMEOUT_MS);
  validated.MAX_RETRIES = Math.max(0, Math.min(5, config.MAX_RETRIES));
  
  return validated;
}

export default FRAME_CONFIG;
