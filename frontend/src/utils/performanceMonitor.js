/**
 * Performance Monitor Utility
 * Tracks frame processing metrics for optimization
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      frameCount: 0,
      detectionCount: 0,
      avgDetectionTime: 0,
      fps: 0,
      lastFrameTime: Date.now(),
      detectionTimes: [],
      errors: 0,
      timeouts: 0
    };
    
    this.maxSamples = 30;  // Keep last 30 samples for averaging
    this.startTime = Date.now();
  }

  /**
   * Record start of detection
   */
  startDetection() {
    this.detectionStartTime = performance.now();
  }

  /**
   * Record end of detection
   */
  endDetection(success = true) {
    if (!this.detectionStartTime) return;
    
    const detectionTime = performance.now() - this.detectionStartTime;
    
    if (success) {
      this.metrics.detectionCount++;
      this.metrics.detectionTimes.push(detectionTime);
      
      // Keep only recent samples
      if (this.metrics.detectionTimes.length > this.maxSamples) {
        this.metrics.detectionTimes.shift();
      }
      
      // Calculate average
      this.metrics.avgDetectionTime = 
        this.metrics.detectionTimes.reduce((a, b) => a + b, 0) / 
        this.metrics.detectionTimes.length;
    }
    
    this.detectionStartTime = null;
  }

  /**
   * Record a frame
   */
  recordFrame() {
    const now = Date.now();
    const timeSinceLastFrame = now - this.metrics.lastFrameTime;
    
    if (timeSinceLastFrame > 0) {
      this.metrics.fps = 1000 / timeSinceLastFrame;
    }
    
    this.metrics.frameCount++;
    this.metrics.lastFrameTime = now;
  }

  /**
   * Record an error
   */
  recordError(type = 'general') {
    this.metrics.errors++;
    if (type === 'timeout') {
      this.metrics.timeouts++;
    }
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    const uptime = (Date.now() - this.startTime) / 1000;  // seconds
    
    return {
      ...this.metrics,
      uptime,
      avgFps: this.metrics.frameCount / uptime,
      successRate: this.metrics.detectionCount / 
        (this.metrics.detectionCount + this.metrics.errors) || 0
    };
  }

  /**
   * Log metrics to console
   */
  logMetrics() {
    const metrics = this.getMetrics();
    console.log('Performance Metrics:', {
      'Frames Processed': metrics.frameCount,
      'Detections': metrics.detectionCount,
      'Avg Detection Time': `${metrics.avgDetectionTime.toFixed(2)}ms`,
      'Current FPS': metrics.fps.toFixed(2),
      'Avg FPS': metrics.avgFps.toFixed(2),
      'Errors': metrics.errors,
      'Timeouts': metrics.timeouts,
      'Success Rate': `${(metrics.successRate * 100).toFixed(1)}%`,
      'Uptime': `${metrics.uptime.toFixed(0)}s`
    });
  }

  /**
   * Reset metrics
   */
  reset() {
    this.metrics = {
      frameCount: 0,
      detectionCount: 0,
      avgDetectionTime: 0,
      fps: 0,
      lastFrameTime: Date.now(),
      detectionTimes: [],
      errors: 0,
      timeouts: 0
    };
    this.startTime = Date.now();
  }

  /**
   * Get performance recommendations
   */
  getRecommendations() {
    const metrics = this.getMetrics();
    const recommendations = [];

    if (metrics.avgDetectionTime > 1000) {
      recommendations.push('Detection time is high - consider using a lighter model');
    }

    if (metrics.avgFps < 5) {
      recommendations.push('Low FPS - increase detection interval or reduce image quality');
    }

    if (metrics.successRate < 0.8) {
      recommendations.push('High error rate - check network connection or API availability');
    }

    if (metrics.timeouts > 5) {
      recommendations.push('Multiple timeouts detected - consider increasing timeout duration');
    }

    return recommendations;
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

export default performanceMonitor;
