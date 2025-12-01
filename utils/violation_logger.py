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

# Import license plate OCR utility
try:
    from utils.license_plate_easyocr import get_ocr_instance
    LICENSE_PLATE_OCR_AVAILABLE = True
    logger.info("License plate OCR available (EasyOCR)")
except ImportError:
    LICENSE_PLATE_OCR_AVAILABLE = False
    logger.warning("License plate OCR not available - install: pip install easyocr")

class ViolationLogger:
    """Handles logging of compliance violations with face detection"""
    
    def __init__(self, log_folder="non_compliance_logs", cooldown_seconds=2, min_face_confidence=35.0):
        self.log_folder = log_folder
        self.logging_enabled = False
        self.cooldown_seconds = cooldown_seconds  # Cooldown period between logs (to prevent rapid spam)
        self.min_face_confidence = min_face_confidence  # Minimum confidence to identify a face
        
        # Track recent violations to prevent duplicate logging
        self.recent_violations = {}  # {violation_hash: timestamp}
        self.last_cleanup_time = time.time()
        
        # Track logged violations per day: {filepath: {"date": date_string, "person": name, "items": [items], "license_plates": [], "model": str}}
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
                    for key, log_info in data.items():
                        # Handle legacy format (person_name as key) vs new format (filepath as key)
                        if isinstance(log_info, dict) and log_info.get("date") == today:
                            # New format - filepath as key
                            cleaned_data[key] = log_info
                        elif isinstance(log_info, str) and log_info == today:
                            # Very old format - skip
                            pass
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
        
        # Clean up old entries and search for person
        for filepath_key, log_info in list(self.logged_today.items()):
            if log_info.get("date") != today:
                del self.logged_today[filepath_key]
            elif log_info.get("person") == person_name:
                return True
        
        return False
    
    def _mark_person_logged_today(self, person_name: str, items: List[str], filepath: str, license_plates: List[str] = None, model_name: str = None):
        """Mark a violation as logged for today (using filepath as key to allow multiple violations per person)"""
        today = date.today().isoformat()
        # Use filepath as the key instead of person_name to allow multiple violations
        self.logged_today[filepath] = {
            "date": today,
            "person": person_name,
            "items": sorted(items),  # Sort for consistent comparison
            "filepath": filepath,
            "license_plates": license_plates or [],  # Store license plate numbers
            "model": model_name or "Unknown"  # Store which model detected this violation
        }
        self._save_daily_logs()
    
    def _has_different_violations(self, person_name: str, current_items: List[str]) -> bool:
        """Check if the current violations are different from previously logged ones for this person"""
        # Search through all files for this person's last logged violations
        for filepath, log_info in self.logged_today.items():
            if log_info.get("person") == person_name:
                logged_items = set(log_info.get("items", []))
                current_items_set = set(sorted(current_items))
                return logged_items != current_items_set
        
        return True  # Not logged before, so it's different
    
    def _delete_previous_log(self, person_name: str):
        """Delete the previous log image and text entry for a person"""
        # Find and delete all files for this person
        files_to_delete = []
        for filepath, log_info in self.logged_today.items():
            if log_info.get("person") == person_name:
                files_to_delete.append((filepath, log_info))
        
        if not files_to_delete:
            return
        
        for filepath_key, log_info in files_to_delete:
            img_filepath = log_info.get("filepath")
            
            # Delete the image file if it exists
            if img_filepath and os.path.exists(img_filepath):
                try:
                    os.remove(img_filepath)
                    logger.info(f"Deleted previous violation image: {img_filepath}")
                except Exception as e:
                    logger.error(f"Error deleting previous image {img_filepath}: {e}")
            
            # Remove from tracking
            if filepath_key in self.logged_today:
                del self.logged_today[filepath_key]
        
        self._save_daily_logs()
    
    def replace_unknown_with_identified(self, identified_name: str, items: List[str], new_filepath: str, model_name: str = None):
        """
        Replace an 'Unknown' log entry with identified person's details.
        Deletes the old Unknown log and updates tracking.
        
        Args:
            identified_name: The newly identified person's name
            items: Non-compliant items detected
            new_filepath: Path to the new violation image
            model_name: Name of the model that detected this violation
        """
        # Delete any previous Unknown logs
        if 'Unknown' in self.logged_today:
            self._delete_previous_log('Unknown')
            logger.info(f"Deleted Unknown log - person identified as: {identified_name}")
        
        # Mark new person as logged
        self._mark_person_logged_today(identified_name, items, new_filepath, model_name=model_name)
    
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
        Check if this violation should be logged based on cooldown period for rapid re-detection.
        
        Note: Logging works with OR without face detection.
        Daily logging limits are handled by main.py session tracking.
        
        Args:
            face_results: List of detected faces (after confidence filtering)
            non_compliant_items: List of non-compliant items
            
        Returns:
            tuple: (bool: should_log, str: reason, bool: should_delete_previous)
        """
        if not self.logging_enabled:
            return False, "Logging disabled", False
        
        # Cleanup old entries periodically
        self._cleanup_old_violations()
        
        # Check cooldown for rapid re-detection (spam prevention)
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
        
        # Allow logging - main.py handles daily limits and session tracking
        return True, "Logging approved", False
    
    def save_violation(self, frame, detections, face_results, compliance_info, current_model=None, skip_cooldown=False):
        """
        Queue a violation to be saved asynchronously (non-blocking).
        Returns immediately without waiting for file I/O.
        
        Args:
            frame: numpy array (BGR) - the video frame
            detections: List of clothing detections
            face_results: List of face detection results
            compliance_info: Dictionary with compliance information
            current_model: Name of the current model (for helmet detection OCR)
            skip_cooldown: If True, bypass cooldown check AND logging enabled check (for manual image uploads)
            
        Returns:
            bool: True if queued for logging, False if not
        """
        # Manual uploads (skip_cooldown=True) bypass logging enabled check
        if not skip_cooldown and not self.logging_enabled:
            logger.warning("save_violation: Logging is disabled (video stream)")
            return False
        
        # Extract non-compliant items
        non_compliant_items = compliance_info.get('non_compliant_items', [])
        
        logger.info(f"save_violation called - Original face_results: {[(f.get('name'), f.get('confidence')) for f in face_results]}")
        
        # Filter faces by confidence threshold
        filtered_faces = self._filter_faces_by_confidence(face_results)
        
        logger.info(f"save_violation - After filtering: {[(f.get('name'), f.get('confidence')) for f in filtered_faces]}")
        
        # Check if we should log this violation (quick check, no I/O)
        with self.lock:
            if skip_cooldown:
                # For manual uploads, skip cooldown check entirely
                logger.info("save_violation - Skipping cooldown/duplicate check (manual upload)")
                should_log = True
                reason = "Manual upload - all checks bypassed"
                should_delete_previous = False
                # Don't update recent_violations for manual uploads to avoid false cooldowns
            else:
                should_log, reason, should_delete_previous = self._should_log_violation(filtered_faces, non_compliant_items)
                logger.info(f"save_violation - should_log: {should_log}, reason: {reason}, should_delete_previous: {should_delete_previous}")
            
            if not should_log:
                logger.warning(f"save_violation: Not logging - {reason}")
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
            should_delete_previous,
            current_model
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
                             non_compliant_items, identified_persons, should_delete_previous, current_model=None):
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
            current_model: Name of the current model (for helmet detection OCR)
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
            
            # Extract license plates ONLY for "Vehicle Helmet" model
            license_plates = []
            is_vehicle_helmet_model = current_model and 'vehicle' in current_model.lower() and 'helmet' in current_model.lower()
            
            if is_vehicle_helmet_model:
                if LICENSE_PLATE_OCR_AVAILABLE:
                    try:
                        # Check if there are helmet violations (no helmet detected)
                        # Support both 'class' and 'label' keys
                        has_helmet_violation = any('helmet' in d.get('class', d.get('label', '')).lower() and 'no' in d.get('class', d.get('label', '')).lower() for d in detections)
                        
                        if has_helmet_violation or True:  # Always try OCR for Vehicle Helmet model
                            logger.info(f"Vehicle Helmet model active - running OCR on license plates...")
                            
                            # Get OCR instance
                            ocr = get_ocr_instance()
                            
                            # Find license plate detections and extract text
                            h_img, w_img = frame.shape[:2]
                            for detection in detections:
                                # Support both 'class' (from detector.py) and 'label' formats
                                label = detection.get('class', detection.get('label', '')).lower()
                                
                                if 'license' in label or 'plate' in label:
                                    # Get bounding box with padding (support both 'bbox' and 'xyxy')
                                    xyxy = detection.get('bbox', detection.get('xyxy', []))
                                    if len(xyxy) == 4:
                                        pad = 5
                                        x1 = max(0, int(xyxy[0]) - pad)
                                        y1 = max(0, int(xyxy[1]) - pad)
                                        x2 = min(w_img, int(xyxy[2]) + pad)
                                        y2 = min(h_img, int(xyxy[3]) + pad)
                                        
                                        # Crop license plate region
                                        lp_crop = frame[y1:y2, x1:x2]
                                        
                                        # Extract text with preprocessing
                                        text = ocr.extract_text(lp_crop, preprocess=True)
                                        
                                        if text:
                                            license_plates.append({
                                                'text': text,
                                                'bbox': xyxy,
                                                'confidence': detection.get('confidence', 0.0)
                                            })
                                            logger.info(f"License plate detected: {text}")
                            
                            if license_plates:
                                logger.info(f"Extracted {len(license_plates)} license plates: {[p['text'] for p in license_plates]}")
                            else:
                                logger.info("No license plates detected in image")
                    except Exception as e:
                        logger.error(f"Error extracting license plates: {e}")
                else:
                    logger.warning("Vehicle Helmet model active but OCR not available - license plates will not be extracted")
                    logger.warning("To enable license plate OCR: pip install easyocr")
            else:
                logger.debug(f"OCR skipped - not Vehicle Helmet model (current: {current_model})")
            
            # Draw compliance boxes (CPU-bound operation)
            annotated_frame = self._draw_compliance_boxes(frame, detections, compliance_info, license_plates)
            
            # Draw face detection boxes
            if face_results:
                annotated_frame = self._draw_face_boxes(annotated_frame, face_results)
            
            # Add metadata overlay (now includes license plates)
            annotated_frame = self._add_metadata_overlay(annotated_frame, compliance_info, face_results, timestamp, license_plates)
            
            # Save the frame (I/O operation)
            cv2.imwrite(filepath, annotated_frame)
            
            # Mark identified persons as logged today (with lock for thread safety)
            # Extract license plate texts for storage
            license_plate_texts = [p['text'] for p in license_plates] if license_plates else []
            
            with self.lock:
                # If no identified persons (face detection disabled or no faces), log as "Unknown"
                persons_to_log = identified_persons if identified_persons else ['Unknown']
                
                for person_name in persons_to_log:
                    self._mark_person_logged_today(person_name, non_compliant_items, filepath, license_plate_texts, model_name=current_model)
                    if license_plate_texts:
                        logger.info(f"Marked {person_name} as logged for today with violations: {', '.join(non_compliant_items)} | Model: {current_model} | License Plates: {', '.join(license_plate_texts)}")
                    else:
                        logger.info(f"Marked {person_name} as logged for today with violations: {', '.join(non_compliant_items)} | Model: {current_model}")
            
            # Log the violation details (I/O operation, now includes license plates)
            self._log_violation_details(filepath, detections, face_results, compliance_info, license_plates)
            
            logger.info(f"Violation logged asynchronously: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving violation asynchronously: {e}", exc_info=True)
    
    def _draw_compliance_boxes(self, frame, detections, compliance_info, license_plates=None):
        """Draw bounding boxes for detected clothing items and license plates"""
        h, w = frame.shape[:2]
        
        non_compliant_items = set(item.lower() for item in compliance_info.get('non_compliant_items', []))
        
        for detection in detections:
            class_name = detection.get('class', '').lower()
            confidence = detection.get('confidence', 0)
            bbox = detection.get('bbox', [])
            
            if len(bbox) != 4:
                continue
            
            # Bbox from detector is already in pixel coordinates, just convert to int
            x_min, y_min, x_max, y_max = bbox
            x_min = int(x_min)
            y_min = int(y_min)
            x_max = int(x_max)
            y_max = int(y_max)
            
            # Check if this is a license plate
            is_plate = 'plate' in class_name or 'number' in class_name or 'license' in class_name
            
            # Color based on compliance
            if class_name in non_compliant_items:
                color = (0, 0, 255)  # Red for non-compliant
                label_bg = (0, 0, 200)
            elif is_plate:
                color = (255, 165, 0)  # Orange for license plates
                label_bg = (200, 100, 0)
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
        
        # Draw license plate text if extracted
        if license_plates:
            for plate in license_plates:
                bbox = plate['bbox']
                text = plate['text']
                x_min, y_min, x_max, y_max = map(int, bbox)
                
                # Draw plate text below the bounding box
                plate_label = f"Plate: {text}"
                label_size, _ = cv2.getTextSize(plate_label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x_min, y_max + 5), 
                             (x_min + label_size[0] + 10, y_max + label_size[1] + 15), 
                             (0, 255, 255), -1)
                cv2.putText(frame, plate_label, (x_min + 5, y_max + label_size[1] + 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def _draw_face_boxes(self, frame, face_results):
        """Draw bounding boxes for detected faces (if bbox available)"""
        for face in face_results:
            # Skip if no bbox (happens when face detection is disabled)
            if 'bbox' not in face:
                logger.debug(f"Skipping face box drawing for {face.get('name', 'Unknown')} - no bbox available")
                continue
                
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
    
    def _add_metadata_overlay(self, frame, compliance_info, face_results, timestamp, license_plates=None):
        """Add metadata overlay at the top of the frame"""
        h, w = frame.shape[:2]
        
        # Adjust overlay height based on content
        overlay_height = 145 if license_plates else 120
        
        # Create semi-transparent overlay background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, overlay_height), (0, 0, 0), -1)
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
        
        # Add license plates if extracted
        if license_plates:
            plates_str = ", ".join([p['text'] for p in license_plates])
            cv2.putText(frame, f"License Plates: {plates_str}", (10, 125), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        return frame
    
    def _log_violation_details(self, filepath, detections, face_results, compliance_info, license_plates=None):
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
                
                # Add license plate info if available
                if license_plates:
                    f.write(f"\nLicense Plates Detected:\n")
                    for plate in license_plates:
                        f.write(f"  - {plate['text']} (Detection Confidence: {plate['confidence']:.2f})\n")
                
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

def get_violation_logger(log_folder="non_compliance_logs", cooldown_seconds=2, min_face_confidence=35.0):
    """Get or create the global violation logger instance"""
    global _violation_logger
    if _violation_logger is None:
        _violation_logger = ViolationLogger(log_folder, cooldown_seconds, min_face_confidence)
    return _violation_logger
