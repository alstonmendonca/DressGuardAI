import cv2
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import numpy as np
import time
import hashlib
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class ViolationLogger:
    """Handles logging of compliance violations with face detection"""
    
    def __init__(self, log_folder="non_compliance_logs", cooldown_seconds=7, min_face_confidence=35.0):
        self.log_folder = log_folder
        self.logging_enabled = False
        self.cooldown_seconds = cooldown_seconds  # Cooldown period between logs
        self.min_face_confidence = min_face_confidence  # Minimum confidence to identify a face
        
        # Track recent violations to prevent duplicate logging
        self.recent_violations = {}  # {violation_hash: timestamp}
        self.last_cleanup_time = time.time()
        
        # Track logged persons per day: {person_name: {"date": date_string, "items": [items], "filepath": path}}
        self.daily_logs_file = os.path.join(log_folder, "daily_logs.json")
        self.logged_today = self._load_daily_logs()
        
        # Thread pool for async processing with limited queue
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ViolationLogger")
        self.pending_tasks = 0  # Track number of pending tasks
        self.max_pending_tasks = 3  # Limit queue size to prevent memory buildup
        self.lock = threading.Lock()
        
        # Create log folder if it doesn't exist
        os.makedirs(log_folder, exist_ok=True)
        logger.info(f"Violation logger initialized. Log folder: {log_folder}, Cooldown: {cooldown_seconds}s, Min confidence: {min_face_confidence}%")
    
    def _load_daily_logs(self) -> Dict[str, Dict]:
        """Load the daily logs tracking file"""
        if os.path.exists(self.daily_logs_file):
            try:
                with open(self.daily_logs_file, 'r') as f:
                    data = json.load(f)
                    # Clean up old entries (not from today)
                    today = date.today().isoformat()
                    cleaned_data = {}
                    for person, log_info in data.items():
                        # Handle both old format (string) and new format (dict)
                        if isinstance(log_info, str):
                            # Old format - just date string
                            if log_info == today:
                                cleaned_data[person] = {"date": today, "items": [], "filepath": None}
                        elif isinstance(log_info, dict) and log_info.get("date") == today:
                            # New format - keep it
                            cleaned_data[person] = log_info
                    return cleaned_data
            except Exception as e:
                logger.error(f"Error loading daily logs: {e}")
        return {}
    
    def _save_daily_logs(self):
        """Save the daily logs tracking file"""
        try:
            with open(self.daily_logs_file, 'w') as f:
                json.dump(self.logged_today, f)
        except Exception as e:
            logger.error(f"Error saving daily logs: {e}")
    
    def _is_person_logged_today(self, person_name: str) -> bool:
        """Check if a person has already been logged today"""
        today = date.today().isoformat()
        
        # Clean up old entries
        if person_name in self.logged_today:
            log_info = self.logged_today[person_name]
            if log_info.get("date") != today:
                del self.logged_today[person_name]
                return False
        
        return person_name in self.logged_today and self.logged_today[person_name].get("date") == today
    
    def _mark_person_logged_today(self, person_name: str, items: List[str], filepath: str):
        """Mark a person as logged for today with violation details"""
        today = date.today().isoformat()
        self.logged_today[person_name] = {
            "date": today,
            "items": sorted(items),  # Sort for consistent comparison
            "filepath": filepath
        }
        self._save_daily_logs()
    
    def _has_different_violations(self, person_name: str, current_items: List[str]) -> bool:
        """Check if the current violations are different from previously logged ones"""
        if person_name not in self.logged_today:
            return True  # Not logged before, so it's different
        
        logged_items = set(self.logged_today[person_name].get("items", []))
        current_items_set = set(sorted(current_items))
        
        return logged_items != current_items_set
    
    def _delete_previous_log(self, person_name: str):
        """Delete the previous log image and text entry for a person"""
        if person_name not in self.logged_today:
            return
        
        filepath = self.logged_today[person_name].get("filepath")
        
        # Delete the image file if it exists
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"Deleted previous violation image: {filepath}")
            except Exception as e:
                logger.error(f"Error deleting previous image {filepath}: {e}")
        
        # Remove from tracking
        del self.logged_today[person_name]
        self._save_daily_logs()
    
    def replace_unknown_with_identified(self, identified_name: str, items: List[str], new_filepath: str):
        """
        Replace an 'Unknown' log entry with identified person's details.
        Deletes the old Unknown log and updates tracking.
        
        Args:
            identified_name: The newly identified person's name
            items: Non-compliant items detected
            new_filepath: Path to the new violation image
        """
        # Delete any previous Unknown logs
        if 'Unknown' in self.logged_today:
            self._delete_previous_log('Unknown')
            logger.info(f"Deleted Unknown log - person identified as: {identified_name}")
        
        # Mark new person as logged
        self._mark_person_logged_today(identified_name, items, new_filepath)
    
    def _filter_faces_by_confidence(self, face_results: List[Dict]) -> List[Dict]:
        """
        Filter faces by minimum confidence and mark low-confidence faces as Unknown.
        
        Args:
            face_results: List of face detection results
            
        Returns:
            List of filtered face results with confidence threshold applied
        """
        filtered_faces = []
        for face in face_results:
            face_copy = face.copy()
            original_name = face_copy['name']
            confidence = face_copy['confidence']
            
            # If confidence is below threshold, mark as Unknown
            if confidence < self.min_face_confidence:
                logger.warning(f"Face confidence too low: {original_name} ({confidence:.1f}%) < {self.min_face_confidence}% - marking as Unknown")
                face_copy['name'] = 'Unknown'
                face_copy['user_id'] = None
            else:
                logger.info(f"Face confidence OK: {original_name} ({confidence:.1f}%) >= {self.min_face_confidence}%")
            
            filtered_faces.append(face_copy)
        return filtered_faces

    
    def enable_logging(self):
        """Enable violation logging"""
        self.logging_enabled = True
        self.recent_violations.clear()  # Clear cache when enabling
        logger.info("Violation logging ENABLED")
    
    def disable_logging(self):
        """Disable violation logging"""
        self.logging_enabled = False
        self.recent_violations.clear()  # Clear cache when disabling
        logger.info("Violation logging DISABLED")
    
    def toggle_logging(self):
        """Toggle logging state"""
        self.logging_enabled = not self.logging_enabled
        if self.logging_enabled:
            self.recent_violations.clear()
        state = "ENABLED" if self.logging_enabled else "DISABLED"
        logger.info(f"Violation logging {state}")
        return self.logging_enabled
    
    def is_logging_enabled(self):
        """Check if logging is currently enabled"""
        return self.logging_enabled
    
    def _generate_violation_hash(self, face_results: List[Dict], non_compliant_items: List[str]) -> str:
        """
        Generate a unique hash for this violation based on detected persons and violations.
        This helps prevent duplicate logging of the same person/violation.
        
        Args:
            face_results: List of detected faces with names
            non_compliant_items: List of non-compliant items
            
        Returns:
            str: Hash representing this unique violation
        """
        # Sort for consistent hashing
        names = sorted([face['name'] for face in face_results])
        items = sorted(non_compliant_items)
        
        # Create a string representation
        violation_str = f"{'-'.join(names)}:{'-'.join(items)}"
        
        # Generate hash
        return hashlib.md5(violation_str.encode()).hexdigest()[:16]
    
    def _cleanup_old_violations(self):
        """Remove violations older than cooldown period"""
        current_time = time.time()
        
        # Only cleanup every 5 seconds to avoid overhead
        if current_time - self.last_cleanup_time < 5:
            return
        
        self.last_cleanup_time = current_time
        expired_keys = [
            key for key, timestamp in self.recent_violations.items()
            if current_time - timestamp > self.cooldown_seconds
        ]
        
        for key in expired_keys:
            del self.recent_violations[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired violation records")
    
    def _should_log_violation(self, face_results: List[Dict], non_compliant_items: List[str]) -> tuple[bool, str, bool]:
        """
        Check if this violation should be logged based on:
        1. No faces detected - do not log
        2. Daily limit - each known person logged once per day UNLESS violations changed
        3. Unknown persons - can be logged multiple times (no daily limit)
        4. Cooldown period for rapid re-detection
        
        Args:
            face_results: List of detected faces (after confidence filtering)
            non_compliant_items: List of non-compliant items
            
        Returns:
            tuple: (bool: should_log, str: reason, bool: should_delete_previous)
        """
        if not self.logging_enabled:
            return False, "Logging disabled", False
        
        # Requirement: Do not log if no faces detected
        if not face_results:
            logger.info("Violation not logged: No faces detected")
            return False, "No faces detected", False
        
        # Cleanup old entries periodically
        self._cleanup_old_violations()
        
        # Get identified persons (non-Unknown)
        identified_persons = [face['name'] for face in face_results if face['name'] != 'Unknown']
        unknown_count = sum(1 for face in face_results if face['name'] == 'Unknown')
        
        # Check if any identified person has already been logged today
        if identified_persons:
            for person_name in identified_persons:
                if self._is_person_logged_today(person_name):
                    # Person logged before - check if violations are different
                    if self._has_different_violations(person_name, non_compliant_items):
                        logger.info(f"Person {person_name} detected with DIFFERENT violations - will update log")
                        # Delete previous log and allow new one
                        return True, "Different violations detected - updating", True
                    else:
                        logger.info(f"Violation not logged: {person_name} already logged today with same violations")
                        return False, f"Already logged today: {person_name}", False
        
        # If only Unknown persons, allow logging (no daily limit for Unknown)
        # Check cooldown for rapid re-detection
        violation_hash = self._generate_violation_hash(face_results, non_compliant_items)
        current_time = time.time()
        
        if violation_hash in self.recent_violations:
            last_log_time = self.recent_violations[violation_hash]
            time_since_last_log = current_time - last_log_time
            
            if time_since_last_log < self.cooldown_seconds:
                logger.debug(f"Violation cooldown active: {self.cooldown_seconds - time_since_last_log:.1f}s remaining")
                return False, "Cooldown active", False
        
        # Update timestamp for this violation
        self.recent_violations[violation_hash] = current_time
        
        return True, "Logging approved", False
    
    def save_violation(self, frame, detections, face_results, compliance_info):
        """
        Queue a violation to be saved asynchronously (non-blocking).
        Returns immediately without waiting for file I/O.
        
        Args:
            frame: numpy array (BGR) - the video frame
            detections: List of clothing detections
            face_results: List of face detection results
            compliance_info: Dictionary with compliance information
            
        Returns:
            bool: True if queued for logging, False if not
        """
        if not self.logging_enabled:
            return False
        
        # Extract non-compliant items
        non_compliant_items = compliance_info.get('non_compliant_items', [])
        
        # Filter faces by confidence threshold
        filtered_faces = self._filter_faces_by_confidence(face_results)
        
        # Check if we should log this violation (quick check, no I/O)
        with self.lock:
            should_log, reason, should_delete_previous = self._should_log_violation(filtered_faces, non_compliant_items)
            if not should_log:
                return False
            
            # Check if queue is full to prevent memory buildup
            if self.pending_tasks >= self.max_pending_tasks:
                logger.warning(f"Violation logging queue full ({self.pending_tasks} pending), skipping frame to prevent lag")
                return False
            
            # Increment pending tasks counter
            self.pending_tasks += 1
        
        # Get identified persons for tracking
        identified_persons = [face['name'] for face in filtered_faces if face['name'] != 'Unknown']
        
        # Make a copy of the frame immediately (before async)
        frame_copy = frame.copy()
        
        # Submit to thread pool for async processing (non-blocking)
        future = self.executor.submit(
            self._save_violation_async,
            frame_copy,
            detections,
            filtered_faces,
            compliance_info,
            non_compliant_items,
            identified_persons,
            should_delete_previous
        )
        
        # Add callback to decrement counter when done
        future.add_done_callback(self._on_task_complete)
        
        logger.debug(f"Violation queued for async logging ({self.pending_tasks} pending)")
        return True
    
    def _on_task_complete(self, future):
        """Callback when async task completes - decrement pending counter"""
        with self.lock:
            self.pending_tasks -= 1
    
    def _save_violation_async(self, frame, detections, face_results, compliance_info, 
                             non_compliant_items, identified_persons, should_delete_previous):
        """
        Internal method to save violation asynchronously (runs in thread pool).
        This is the actual I/O heavy work that runs in background.
        
        Args:
            frame: numpy array (BGR) - the video frame (already copied)
            detections: List of clothing detections
            face_results: List of face detection results (filtered)
            compliance_info: Dictionary with compliance information
            non_compliant_items: List of non-compliant items
            identified_persons: List of identified person names
            should_delete_previous: Whether to delete previous logs
        """
        try:
            # Delete previous logs if violations changed (I/O operation)
            if should_delete_previous and identified_persons:
                with self.lock:
                    for person_name in identified_persons:
                        self._delete_previous_log(person_name)
            
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"violation_{timestamp}.jpg"
            filepath = os.path.join(self.log_folder, filename)
            
            # Draw compliance boxes (CPU-bound operation)
            annotated_frame = self._draw_compliance_boxes(frame, detections, compliance_info)
            
            # Draw face detection boxes
            if face_results:
                annotated_frame = self._draw_face_boxes(annotated_frame, face_results)
            
            # Add metadata overlay
            annotated_frame = self._add_metadata_overlay(annotated_frame, compliance_info, face_results, timestamp)
            
            # Save the frame (I/O operation)
            cv2.imwrite(filepath, annotated_frame)
            
            # Mark identified persons as logged today (with lock for thread safety)
            with self.lock:
                for person_name in identified_persons:
                    self._mark_person_logged_today(person_name, non_compliant_items, filepath)
                    logger.info(f"Marked {person_name} as logged for today with violations: {', '.join(non_compliant_items)}")
            
            # Log the violation details (I/O operation)
            self._log_violation_details(filepath, detections, face_results, compliance_info)
            
            logger.info(f"Violation logged asynchronously: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving violation asynchronously: {e}", exc_info=True)
    
    def _draw_compliance_boxes(self, frame, detections, compliance_info):
        """Draw bounding boxes for detected clothing items"""
        h, w = frame.shape[:2]
        
        non_compliant_items = set(item.lower() for item in compliance_info.get('non_compliant_items', []))
        
        for detection in detections:
            class_name = detection.get('class', '').lower()
            confidence = detection.get('confidence', 0)
            bbox = detection.get('bbox', [])
            
            if len(bbox) != 4:
                continue
            
            # Denormalize coordinates
            x_min, y_min, x_max, y_max = bbox
            x_min = int(x_min * w)
            y_min = int(y_min * h)
            x_max = int(x_max * w)
            y_max = int(y_max * h)
            
            # Color based on compliance
            if class_name in non_compliant_items:
                color = (0, 0, 255)  # Red for non-compliant
                label_bg = (0, 0, 200)
            else:
                color = (0, 255, 0)  # Green for compliant
                label_bg = (0, 200, 0)
            
            # Draw rectangle
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
            
            # Draw label
            label = f"{detection['class']} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x_min, y_min - label_size[1] - 10), 
                         (x_min + label_size[0], y_min), label_bg, -1)
            cv2.putText(frame, label, (x_min, y_min - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
    
    def _draw_face_boxes(self, frame, face_results):
        """Draw bounding boxes for detected faces"""
        for face in face_results:
            top, right, bottom, left = face['bbox']
            name = face['name']
            confidence = face['confidence']
            
            # Choose color based on recognition
            if name == "Unknown":
                color = (0, 165, 255)  # Orange for unknown
                label_bg = (0, 140, 255)
            else:
                color = (255, 0, 255)  # Magenta for recognized
                label_bg = (200, 0, 200)
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            # Draw label background
            label = f"FACE: {name} ({confidence:.1f}%)"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (left, bottom), 
                         (left + label_size[0] + 10, bottom + label_size[1] + 10), 
                         label_bg, -1)
            
            # Draw label text
            cv2.putText(frame, label, (left + 5, bottom + label_size[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _add_metadata_overlay(self, frame, compliance_info, face_results, timestamp):
        """Add metadata overlay at the top of the frame"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Add title
        cv2.putText(frame, "COMPLIANCE VIOLATION LOG", (10, 25), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
        
        # Add timestamp
        time_str = datetime.strptime(timestamp, "%Y%m%d_%H%M%S_%f").strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Time: {time_str}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add non-compliant items
        non_compliant = compliance_info.get('non_compliant_items', [])
        if non_compliant:
            items_str = ", ".join(non_compliant)
            cv2.putText(frame, f"Violations: {items_str}", (10, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        
        # Add identified persons
        if face_results:
            names = [f['name'] for f in face_results]
            names_str = ", ".join(names)
            cv2.putText(frame, f"Persons: {names_str}", (10, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        return frame
    
    def _log_violation_details(self, filepath, detections, face_results, compliance_info):
        """Write violation details to a text log file"""
        log_file = os.path.join(self.log_folder, "violation_log.txt")
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Violation logged: {os.path.basename(filepath)}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nNon-Compliant Items:\n")
                for item in compliance_info.get('non_compliant_items', []):
                    f.write(f"  - {item}\n")
                
                f.write(f"\nIdentified Persons:\n")
                if face_results:
                    for face in face_results:
                        f.write(f"  - {face['name']} (Confidence: {face['confidence']:.1f}%)\n")
                else:
                    f.write("  - No faces detected\n")
                
                f.write(f"\nAll Detections:\n")
                for det in detections:
                    f.write(f"  - {det['class']}: {det['confidence']:.2f}\n")
                
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
    
    def get_stats(self) -> Dict:
        """Get violation logger statistics"""
        today = date.today().isoformat()
        logged_count = sum(1 for d in self.logged_today.values() if d == today)
        
        return {
            "logging_enabled": self.logging_enabled,
            "cooldown_seconds": self.cooldown_seconds,
            "min_face_confidence": self.min_face_confidence,
            "active_violations": len(self.recent_violations),
            "persons_logged_today": logged_count,
            "log_folder": self.log_folder
        }
    
    def set_cooldown(self, seconds: int):
        """Update cooldown period"""
        self.cooldown_seconds = max(1, seconds)  # Minimum 1 second
        logger.info(f"Violation logger cooldown set to {self.cooldown_seconds}s")

# Global instance
_violation_logger = None

def get_violation_logger(log_folder="non_compliance_logs", cooldown_seconds=10, min_face_confidence=47.0):
    """Get or create the global violation logger instance"""
    global _violation_logger
    if _violation_logger is None:
        _violation_logger = ViolationLogger(log_folder, cooldown_seconds, min_face_confidence)
    return _violation_logger
