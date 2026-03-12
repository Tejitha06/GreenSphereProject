"""
Unified Plant Growth Tracking System
=====================================
Efficiently integrates:
- Plant.id API (species identification)
- Rembg (fast background removal/segmentation)
- PlantCV (scientific measurements)
- Gemini AI (intelligent report generation)

Optimized for:
- Memory efficiency (lazy loading)
- Parallel processing where possible
- Graceful degradation
- Comprehensive error handling
"""

import cv2
import numpy as np
from datetime import datetime, timezone
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging
import json
import os
import time
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def to_python_type(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_python_type(item) for item in obj]
    return obj


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SegmentationResult:
    """Result from plant segmentation"""
    success: bool
    mask: Optional[np.ndarray] = None
    foreground: Optional[np.ndarray] = None
    confidence: float = 0.0
    method: str = "unknown"
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class MeasurementResult:
    """Result from plant measurements"""
    success: bool
    height_px: float = 0.0
    width_px: float = 0.0
    area_px: float = 0.0
    perimeter_px: float = 0.0
    height_cm: Optional[float] = None
    width_cm: Optional[float] = None
    area_cm2: Optional[float] = None
    greenness_index: float = 0.0
    health_score: float = 0.0
    leaf_count_estimate: Optional[int] = None
    color_histogram: Dict[str, Any] = field(default_factory=dict)
    advanced_metrics: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class SpeciesResult:
    """Result from species identification"""
    success: bool
    name: str = "Unknown"
    scientific_name: str = "Unknown"
    confidence: float = 0.0
    common_names: List[str] = field(default_factory=list)
    care_info: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class GrowthReport:
    """Comprehensive plant health and growth report"""
    success: bool
    # All fields below have defaults
    timestamp: str = ""
    image_hash: str = ""
    # Component results
    segmentation: Optional[SegmentationResult] = None
    measurements: Optional[MeasurementResult] = None
    species: Optional[SpeciesResult] = None
    # Species verification
    species_verified: bool = True
    species_mismatch_reason: Optional[str] = None
    # User-facing health and growth fields
    health_summary: str = ""
    care_recommendations: List[str] = field(default_factory=list)
    growth_forecast: str = ""
    issues_detected: List[str] = field(default_factory=list)
    growth_trend_analysis: str = ""
    shape_and_structure_analysis: str = ""
    metrics_interpretation: Dict[str, Any] = field(default_factory=dict)
    species_care_profile: Dict[str, Any] = field(default_factory=dict)
    # AI-generated fields
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None
    ai_growth_forecast: Optional[str] = None
    ai_issues_detected: Optional[List[str]] = None
    ai_trend_analysis: Optional[str] = None
    ai_shape_analysis: Optional[str] = None
    ai_metrics_interpretation: Dict[str, Any] = field(default_factory=dict)
    species_parameters: Dict[str, Any] = field(default_factory=dict)
    # Comparison with previous
    growth_delta: Dict[str, Any] = field(default_factory=dict)
    # Plant diary/history: list of dicts with timestamp, image, and all tracked metrics
    plant_diary: List[Dict[str, Any]] = field(default_factory=list)
    # History context
    history_record_count: int = 0
    # Metadata
    total_processing_time_ms: float = 0.0
    components_used: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
# REMBG SEGMENTATION (Fast Background Removal)
# ============================================================================

class RembgSegmenter:
    """
    Fast plant segmentation using Rembg.
    Falls back to color-based segmentation if Rembg unavailable.
    """
    
    def __init__(self, model_name: str = "u2net"):
        """
        Initialize Rembg segmenter.
        
        Args:
            model_name: Model to use ('u2net', 'u2netp', 'u2net_human_seg', 'isnet-general-use')
        """
        self.model_name = model_name
        self._session = None
        self._rembg_available = None
        logger.info("RembgSegmenter initialized with model: %s", model_name)
    
    @property
    def rembg_available(self) -> bool:
        """Lazy check for rembg availability"""
        if self._rembg_available is None:
            try:
                import importlib.util
                if importlib.util.find_spec("rembg"):
                    self._rembg_available = True
                    logger.info("✅ Rembg is available")
                else:
                    self._rembg_available = False
                    logger.warning("⚠️ Rembg not available, using fallback segmentation")
            except ImportError:
                self._rembg_available = False
                logger.warning("⚠️ Rembg not available, using fallback segmentation")
        return self._rembg_available
    
    def segment(self, image: np.ndarray) -> SegmentationResult:
        """
        Segment plant from background.
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            SegmentationResult with mask and foreground
        """
        start_time = time.time()
        
        try:
            if self.rembg_available:
                return self._segment_rembg(image, start_time)
            else:
                return self._segment_color_fallback(image, start_time)
        except Exception as e:
            logger.error(f"Segmentation error: {e}")
            return SegmentationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _segment_rembg(self, image: np.ndarray, start_time: float) -> SegmentationResult:
        """Segment using Rembg (preferred method)"""
        import rembg
        from PIL import Image
        
        # Convert BGR to RGB for Rembg
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Remove background
        output = rembg.remove(
            pil_image,
            session=self._get_or_create_session(),
            only_mask=False,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10
        )
        
        # Convert result back to numpy
        output_np = np.array(output)
        
        # Extract alpha channel as mask
        if output_np.shape[2] == 4:
            alpha = output_np[:, :, 3]
            mask = (alpha > 128).astype(np.uint8)
            foreground = cv2.cvtColor(output_np[:, :, :3], cv2.COLOR_RGB2BGR)
        else:
            # Fallback if no alpha
            mask = np.ones(image.shape[:2], dtype=np.uint8)
            foreground = image.copy()
        
        # Calculate confidence based on mask coverage
        coverage = np.sum(mask) / mask.size
        confidence = min(0.95, 0.5 + coverage * 0.5) if 0.01 < coverage < 0.95 else 0.7
        
        return SegmentationResult(
            success=True,
            mask=mask,
            foreground=foreground,
            confidence=confidence,
            method="rembg",
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def _segment_color_fallback(self, image: np.ndarray, start_time: float) -> SegmentationResult:
        """Color-based segmentation fallback when Rembg unavailable"""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define green range (typical plant colors)
        lower_green = np.array([25, 30, 30])
        upper_green = np.array([95, 255, 255])
        
        # Create mask
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Fill holes
        mask = self._fill_holes(mask)
        
        # Apply mask to get foreground
        foreground = cv2.bitwise_and(image, image, mask=mask)
        
        # Binary mask
        mask = (mask > 0).astype(np.uint8)
        
        return SegmentationResult(
            success=True,
            mask=mask,
            foreground=foreground,
            confidence=0.75,  # Lower confidence for fallback
            method="color_fallback",
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def _fill_holes(self, mask: np.ndarray) -> np.ndarray:
        """Fill holes in binary mask"""
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Fill all contours
            filled = np.zeros_like(mask)
            cv2.drawContours(filled, contours, -1, 255, -1)
            return filled
        return mask
    
    def _get_or_create_session(self):
        """Get or create Rembg session for efficiency"""
        if self._session is None:
            import rembg
            self._session = rembg.new_session(self.model_name)
        return self._session


# ============================================================================
# PLANTCV MEASUREMENTS (Scientific Plant Analysis)
# ============================================================================

class PlantCVAnalyzer:
    """
    Scientific plant measurements using PlantCV.
    Falls back to OpenCV-based measurements if PlantCV unavailable.
    """
    
    def __init__(self, pixels_per_cm: float = None):
        """
        Initialize PlantCV analyzer.
        
        Args:
            pixels_per_cm: Scale factor for real-world measurements
        """
        self.pixels_per_cm = pixels_per_cm
        self._plantcv_available = None
        logger.info("PlantCVAnalyzer initialized")
    
    @property
    def plantcv_available(self) -> bool:
        """Lazy check for PlantCV availability"""
        if self._plantcv_available is None:
            try:
                import importlib.util
                if importlib.util.find_spec("plantcv"):
                    self._plantcv_available = True
                    logger.info("✅ PlantCV is available")
                else:
                    self._plantcv_available = False
                    logger.warning("⚠️ PlantCV not available, using OpenCV fallback")
            except ImportError:
                self._plantcv_available = False
                logger.warning("⚠️ PlantCV not available, using OpenCV fallback")
        return self._plantcv_available
    
    def measure(self, image: np.ndarray, mask: np.ndarray) -> MeasurementResult:
        """
        Measure plant features.
        
        Args:
            image: Original image (BGR)
            mask: Binary segmentation mask
            
        Returns:
            MeasurementResult with comprehensive measurements
        """
        start_time = time.time()
        
        try:
            if self.plantcv_available:
                result = self._measure_plantcv(image, mask)
            else:
                result = self._measure_opencv(image, mask)
            
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Measurement error: {e}")
            return MeasurementResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _measure_plantcv(self, image: np.ndarray, mask: np.ndarray) -> MeasurementResult:
        """Measure using PlantCV 4.x API with full feature utilization"""
        from plantcv import plantcv as pcv
        
        # Configure PlantCV
        pcv.params.debug = None
        pcv.outputs.clear()
        
        # Ensure mask is proper format (binary 0/255)
        mask_uint8 = (mask * 255).astype(np.uint8) if mask.max() <= 1 else mask.astype(np.uint8)
        
        # Apply morphological operations to improve mask quality
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
        # Close small gaps, then open to remove noise
        mask_clean = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel_large, iterations=2)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel_small, iterations=1)
        
        # Fill holes in the mask
        contours_fill, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_fill:
            cv2.drawContours(mask_clean, contours_fill, -1, 255, -1)
        
        # Find contours
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            logger.warning("No contours found in PlantCV, falling back to OpenCV")
            return self._measure_opencv(image, mask)
        
        # Calculate total image area for minimum threshold
        img_area = image.shape[0] * image.shape[1]
        min_contour_area = img_area * 0.005  # At least 0.5% of image for significant detection
        
        # Filter significant contours
        significant_contours = [c for c in contours if cv2.contourArea(c) > min_contour_area]
        
        if not significant_contours:
            # Use largest contour if none pass threshold
            significant_contours = [max(contours, key=cv2.contourArea)]
        
        # Create combined binary mask from all significant contours
        combined_mask = np.zeros(mask_clean.shape, dtype=np.uint8)
        cv2.drawContours(combined_mask, significant_contours, -1, 255, -1)
        
        # Create labeled mask for PlantCV 4.x (uses 1, 2, 3... for labels, not 255)
        labeled_mask = np.zeros(mask_clean.shape, dtype=np.uint8)
        cv2.drawContours(labeled_mask, significant_contours, -1, 1, -1)
        
        # ===== PlantCV ANALYZE.SIZE - Full shape metrics =====
        try:
            pcv.analyze.size(img=image, labeled_mask=labeled_mask, n_labels=1)
        except Exception as e:
            logger.warning(f"PlantCV analyze.size failed: {e}")
        
        # ===== PlantCV ANALYZE.COLOR - Color distribution =====
        try:
            pcv.analyze.color(
                rgb_img=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
                labeled_mask=labeled_mask,
                n_labels=1,
                colorspaces="hsv"
            )
        except Exception as e:
            logger.warning(f"PlantCV analyze.color failed: {e}")
        
        # ===== PlantCV MORPHOLOGY - Leaf tip counting =====
        leaf_count_tips = 0
        try:
            # Skeletonize the mask for morphological analysis
            skeleton = pcv.morphology.skeletonize(mask=combined_mask)
            
            # Find tips (leaf endpoints)
            tips_img = pcv.morphology.find_tips(skel_img=skeleton, mask=combined_mask)
            leaf_count_tips = np.sum(tips_img > 0)  # Count white pixels (tips)
            
            # Find branch points for more structure info
            try:
                branch_pts = pcv.morphology.find_branch_pts(skel_img=skeleton, mask=combined_mask)
                branch_count = np.sum(branch_pts > 0)
            except Exception:
                branch_count = 0
        except Exception as e:
            logger.warning(f"PlantCV morphology failed: {e}")
            leaf_count_tips = 0
            branch_count = 0
        
        # ===== Extract measurements from PlantCV outputs =====
        observations = pcv.outputs.observations
        
        # Initialize with defaults
        area = 0
        perimeter = 0
        height = 0
        width = 0
        solidity = 0
        convex_hull_area = 0
        longest_path = 0
        ellipse_major = 0
        ellipse_minor = 0
        ellipse_angle = 0
        ellipse_eccentricity = 0
        center_x, center_y = 0, 0
        
        # Extract all available metrics from PlantCV observations
        if observations:
            # PlantCV 4.x stores observations with label keys like 'default_1'
            for key, obs_dict in observations.items():
                if isinstance(obs_dict, dict):
                    # Size metrics
                    if 'area' in obs_dict:
                        area = obs_dict['area'].get('value', 0) or 0
                    if 'perimeter' in obs_dict:
                        perimeter = obs_dict['perimeter'].get('value', 0) or 0
                    if 'height' in obs_dict:
                        height = obs_dict['height'].get('value', 0) or 0
                    if 'width' in obs_dict:
                        width = obs_dict['width'].get('value', 0) or 0
                    if 'solidity' in obs_dict:
                        solidity = obs_dict['solidity'].get('value', 0) or 0
                    if 'convex_hull_area' in obs_dict:
                        convex_hull_area = obs_dict['convex_hull_area'].get('value', 0) or 0
                    if 'longest_path' in obs_dict:
                        longest_path = obs_dict['longest_path'].get('value', 0) or 0
                    
                    # Ellipse metrics (better for plant shape)
                    if 'ellipse_major_axis' in obs_dict:
                        ellipse_major = obs_dict['ellipse_major_axis'].get('value', 0) or 0
                    if 'ellipse_minor_axis' in obs_dict:
                        ellipse_minor = obs_dict['ellipse_minor_axis'].get('value', 0) or 0
                    if 'ellipse_angle' in obs_dict:
                        ellipse_angle = obs_dict['ellipse_angle'].get('value', 0) or 0
                    if 'ellipse_eccentricity' in obs_dict:
                        ellipse_eccentricity = obs_dict['ellipse_eccentricity'].get('value', 0) or 0
                    
                    # Center of mass
                    if 'center_of_mass' in obs_dict:
                        com = obs_dict['center_of_mass'].get('value', (0, 0))
                        if isinstance(com, (list, tuple)) and len(com) >= 2:
                            center_x, center_y = int(com[0]), int(com[1])
        
        # Fallback to OpenCV if PlantCV didn't return size values
        if height == 0 or width == 0:
            all_points = np.vstack(significant_contours)
            x, y, w, h = cv2.boundingRect(all_points)
            height = h
            width = w
            center_x = int(x + w/2)
            center_y = int(y + h/2)
        
        if area == 0:
            area = sum(cv2.contourArea(c) for c in significant_contours)
        
        if perimeter == 0:
            perimeter = sum(cv2.arcLength(c, True) for c in significant_contours)
        
        # ===== Calculate greenness index from HSV =====
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # Expanded green range to capture more plant colors
        green_mask = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([95, 255, 255]))
        plant_pixels = np.sum(combined_mask > 0)
        plant_green = cv2.bitwise_and(green_mask, green_mask, mask=combined_mask)
        greenness = np.sum(plant_green > 0) / plant_pixels if plant_pixels > 0 else 0
        
        # ===== Estimate leaf count =====
        # Use PlantCV tips if available, otherwise fall back to watershed
        if leaf_count_tips > 0:
            leaf_count = max(1, leaf_count_tips // 2)  # Tips often overcount, adjust
        else:
            leaf_count = self._estimate_leaf_count(combined_mask)
        
        # ===== Calculate health score =====
        health_score = self._calculate_health_score(image, combined_mask)
        
        # ===== Color histogram =====
        color_hist = self._get_color_histogram(image, combined_mask)
        
        # ===== Convert all numpy types to Python native =====
        height = int(height)
        width = int(width)
        area = float(area)
        perimeter = float(perimeter)
        leaf_count = int(leaf_count)
        leaf_count_tips = int(leaf_count_tips)
        branch_count = int(branch_count) if 'branch_count' in dir() and branch_count else 0
        center_x = int(center_x)
        center_y = int(center_y)
        
        # ===== Build result =====
        result = MeasurementResult(
            success=True,
            height_px=float(height),
            width_px=float(width),
            area_px=float(area),
            perimeter_px=float(perimeter),
            leaf_count_estimate=leaf_count,
            greenness_index=float(greenness),
            health_score=float(health_score),
            color_histogram=to_python_type(color_hist),
            advanced_metrics={
                # Shape metrics
                'solidity': float(solidity),
                'convex_hull_area': float(convex_hull_area),
                'longest_path': float(longest_path),
                'aspect_ratio': float(width) / float(height) if height > 0 else 0.0,
                
                # Ellipse-based measurements (more accurate for plants)
                'ellipse_major_axis': float(ellipse_major),
                'ellipse_minor_axis': float(ellipse_minor),
                'ellipse_angle': float(ellipse_angle),
                'ellipse_eccentricity': float(ellipse_eccentricity),
                
                # Morphology metrics
                'leaf_tips_detected': leaf_count_tips,
                'branch_points': branch_count,
                
                # Position
                'center_of_mass': {'x': center_x, 'y': center_y},
                'bounding_box': {
                    'x': int(center_x - width/2), 
                    'y': int(center_y - height/2), 
                    'w': width, 
                    'h': height
                },
                
                # Analysis metadata
                'analysis_method': 'plantcv_4x_full',
                'contours_analyzed': len(significant_contours),
                'mask_coverage_pct': float(plant_pixels / img_area * 100)
            }
        )
        
        # Add real-world measurements if scale available
        if self.pixels_per_cm:
            result.height_cm = result.height_px / self.pixels_per_cm
            result.width_cm = result.width_px / self.pixels_per_cm
            result.area_cm2 = result.area_px / (self.pixels_per_cm ** 2)
        
        logger.info(f"PlantCV analysis complete: {width}x{height}px, {leaf_count} leaves, {health_score:.0f}% health")
        return result
    
    def _measure_opencv(self, image: np.ndarray, mask: np.ndarray) -> MeasurementResult:
        """Measure using OpenCV (fallback) - improved to match PlantCV quality"""
        # Ensure mask is proper format
        mask_uint8 = (mask * 255).astype(np.uint8) if mask.max() <= 1 else mask.astype(np.uint8)
        
        # Apply morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Fill holes
        contours_fill, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_fill:
            cv2.drawContours(mask_clean, contours_fill, -1, 255, -1)
        
        # Find contours
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return MeasurementResult(success=False, error="No contours found")
        
        # Filter and combine significant contours
        img_area = image.shape[0] * image.shape[1]
        min_area = img_area * 0.005
        significant = [c for c in contours if cv2.contourArea(c) > min_area]
        if not significant:
            significant = [max(contours, key=cv2.contourArea)]
        
        # Create combined mask
        combined_mask = np.zeros(mask_clean.shape, dtype=np.uint8)
        cv2.drawContours(combined_mask, significant, -1, 255, -1)
        
        # Get bounding box of all significant contours
        all_points = np.vstack(significant)
        x, y, w, h = cv2.boundingRect(all_points)
        
        # Total area and perimeter
        area = sum(cv2.contourArea(c) for c in significant)
        perimeter = sum(cv2.arcLength(c, True) for c in significant)
        
        # Greenness index with expanded green range
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([95, 255, 255]))
        plant_pixels = np.sum(combined_mask > 0)
        plant_green = cv2.bitwise_and(green_mask, green_mask, mask=combined_mask)
        greenness = np.sum(plant_green > 0) / plant_pixels if plant_pixels > 0 else 0
        
        # Estimate leaves
        leaf_count = self._estimate_leaf_count(combined_mask)
        
        # Health score
        health_score = self._calculate_health_score(image, combined_mask)
        
        # Color histogram
        color_hist = self._get_color_histogram(image, combined_mask)
        
        # Convex hull for solidity
        hull = cv2.convexHull(all_points)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        result = MeasurementResult(
            success=True,
            height_px=float(h),
            width_px=float(w),
            area_px=float(area),
            perimeter_px=float(perimeter),
            leaf_count_estimate=leaf_count,
            greenness_index=float(greenness),
            health_score=health_score,
            color_histogram=color_hist,
            advanced_metrics={
                'solidity': float(solidity),
                'convex_hull_area': float(hull_area),
                'aspect_ratio': float(w) / float(h) if h > 0 else 0,
                'center_of_mass': {'x': int(x + w/2), 'y': int(y + h/2)},
                'bounding_box': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
                'analysis_method': 'opencv_improved',
                'contours_analyzed': len(significant),
                'mask_coverage_pct': float(plant_pixels / img_area * 100)
            }
        )
        
        if self.pixels_per_cm:
            result.height_cm = result.height_px / self.pixels_per_cm
            result.width_cm = result.width_px / self.pixels_per_cm
            result.area_cm2 = result.area_px / (self.pixels_per_cm ** 2)
        
        logger.info(f"OpenCV analysis complete: {w}x{h}px, {leaf_count} leaves, {health_score:.0f}% health")
        return result
    
    def _estimate_leaf_count(self, mask: np.ndarray) -> int:
        """Estimate leaf count using watershed or contour analysis"""
        try:
            # Distance transform
            dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            
            # Normalize and threshold
            dist_norm = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            _, peaks = cv2.threshold(dist_norm, 0.5 * dist_norm.max(), 255, cv2.THRESH_BINARY)
            
            # Find connected components (potential leaf centers)
            n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(peaks.astype(np.uint8))
            
            # Filter by size
            min_size = mask.shape[0] * mask.shape[1] * 0.001
            valid_labels = np.sum([1 for stat in stats[1:] if stat[4] > min_size])
            
            return max(1, min(valid_labels, 50))  # Cap at reasonable number
            
        except Exception:
            return 5  # Default estimate
    
    def _calculate_health_score(self, image: np.ndarray, mask: np.ndarray) -> float:
        """Calculate plant health score (0-100)"""
        try:
            # Extract plant pixels
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Get mean values in plant region
            h_mean = np.mean(hsv[:, :, 0][mask > 0])
            s_mean = np.mean(hsv[:, :, 1][mask > 0])
            v_mean = np.mean(hsv[:, :, 2][mask > 0])
            
            # Score components
            # Hue: ideal green is around 60 (in OpenCV scale 0-180)
            hue_score = 100 - abs(60 - h_mean) * 2 if h_mean is not None else 0
            hue_score = max(0, min(100, hue_score))

            # Saturation: higher is healthier (more vivid)
            sat_score = (s_mean / 255) * 100 if s_mean is not None else 0

            # Value: medium-high is ideal
            val_score = 100 - abs(180 - v_mean) * 0.5 if v_mean is not None else 0
            val_score = max(0, min(100, val_score))

            # Yellowing detection (penalty)
            yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([35, 255, 255]))
            yellow_in_plant = cv2.bitwise_and(yellow_mask, yellow_mask, mask=mask)
            yellow_ratio = np.sum(yellow_in_plant > 0) / np.sum(mask > 0) if np.sum(mask > 0) > 0 else 0
            yellow_penalty = yellow_ratio * 30 if yellow_ratio is not None else 0

            # Brown/dead detection (penalty)
            brown_mask = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 200, 150]))
            brown_in_plant = cv2.bitwise_and(brown_mask, brown_mask, mask=mask)
            brown_ratio = np.sum(brown_in_plant > 0) / np.sum(mask > 0) if np.sum(mask > 0) > 0 else 0
            brown_penalty = brown_ratio * 40 if brown_ratio is not None else 0

            # Combined score
            try:
                health = (hue_score * 0.4 + sat_score * 0.3 + val_score * 0.3) - yellow_penalty - brown_penalty
            except Exception as e:
                logger.error(f"Health calculation error: {e}")
                health = 50.0

            return max(0, min(100, health))
            
        except Exception:
            return 50.0  # Default neutral score
    
    def _get_color_histogram(self, image: np.ndarray, mask: np.ndarray) -> Dict[str, Any]:
        """Get color histogram data"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate histograms
            h_hist = cv2.calcHist([hsv], [0], mask, [18], [0, 180])
            s_hist = cv2.calcHist([hsv], [1], mask, [8], [0, 256])
            v_hist = cv2.calcHist([hsv], [2], mask, [8], [0, 256])
            
            return {
                'hue_distribution': [float(x[0]) for x in h_hist],
                'saturation_distribution': [float(x[0]) for x in s_hist],
                'value_distribution': [float(x[0]) for x in v_hist],
                'dominant_hue': float(np.argmax(h_hist) * 10),
                'mean_saturation': float(np.mean(hsv[:, :, 1][mask > 0])) if np.sum(mask) > 0 else 0,
                'mean_value': float(np.mean(hsv[:, :, 2][mask > 0])) if np.sum(mask) > 0 else 0
            }
            
        except Exception:
            return {}


# ============================================================================
# GEMINI AI REPORTER (Intelligent Analysis)
# ============================================================================

class GeminiReporter:
    """
    Generate intelligent plant analysis reports using Gemini AI.
    Falls back to template-based reports if API unavailable.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    
    def __init__(self, api_keys: List[str] = None):
        """
        Initialize Gemini reporter.
        
        Args:
            api_keys: List of Gemini API keys for rotation
        """
        self.api_keys = api_keys or self._load_api_keys()
        self._current_key_idx = 0
        logger.info(f"GeminiReporter initialized with {len(self.api_keys)} API keys")
    
    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment"""
        keys_str = os.getenv('GEMINI_API_KEYS', '')
        if keys_str:
            return [k.strip() for k in keys_str.split(',') if k.strip()]
        
        single_key = os.getenv('GEMINI_API_KEY', '')
        return [single_key] if single_key else []
    
    def generate_report(
        self,
        species: Optional[SpeciesResult],
        measurements: Optional[MeasurementResult],
        previous_measurements: Optional[MeasurementResult] = None,
        plant_name: str = None,
        growth_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered analysis report with history context.
        
        Args:
            species: Species identification result
            measurements: Current measurements
            previous_measurements: Previous measurements for comparison
            plant_name: Optional custom plant name
            growth_history: List of past measurements for trend analysis
            
        Returns:
            Dict with AI summary, recommendations, etc.
        """
        start_time = time.time()
        
        try:
            if self.api_keys:
                return self._generate_gemini_report(
                    species, measurements, previous_measurements, plant_name, start_time, growth_history
                )
            else:
                return self._generate_template_report(
                    species, measurements, previous_measurements, plant_name, start_time, growth_history
                )
                
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return self._generate_template_report(
                species, measurements, previous_measurements, plant_name, start_time, growth_history
            )
    
    def _generate_gemini_report(
        self, 
        species: Optional[SpeciesResult],
        measurements: Optional[MeasurementResult],
        previous_measurements: Optional[MeasurementResult],
        plant_name: str,
        start_time: float,
        growth_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate report using Gemini API with full history context"""
        import requests
        
        # Build context for AI including history
        context = self._build_context(species, measurements, previous_measurements, plant_name, growth_history)
        
        # Get scientific name for species-specific advice
        scientific_name = species.scientific_name if species and species.scientific_name else ""
        species_display = species.name if species and species.name else plant_name
        
        prompt = f"""
You are a professional horticulturist and plant scientist. Provide a DETAILED, metric-driven analysis and care plan for the plant below, using ONLY peer-reviewed botanical research and trusted sources.

CRITICAL: Base ALL recommendations on the SCIENTIFIC NAME: {scientific_name}
Use knowledge from these trusted sources ONLY:
- Royal Horticultural Society (RHS)
- Missouri Botanical Garden
- Kew Gardens
- University agricultural extension services (UC Davis, Cornell, etc.)
- USDA Plant Database
- American Horticultural Society
- International Society for Horticultural Science

PLANT SCIENTIFIC NAME: {scientific_name}
COMMON NAME: {species_display}

PLANT DATA AND HISTORY:
{context}

IMPORTANT: The following PlantCV metrics were measured for this plant. For each, provide a detailed interpretation, compare to documented norms for {scientific_name}, and explain what each value means for health, growth, and care:

- Solidity
- Eccentricity
- Aspect Ratio
- Convex Hull Area
- Leaf Tips Detected
- Branch Points
- Fitted Ellipse (major/minor axis, angle)
- Center of Mass
- Bounding Box
- Longest Skeleton Path
- Mask Coverage %
- Color Histogram (hue, saturation, value)
- Greenness Index
- Health Score
- Estimated Real Size (height, width, area in cm)
- Perimeter
- Estimated Leaf Count
- Any other PlantCV/advanced metrics present

For each metric, do ALL of the following:
- State the measured value
- Explain what it means for this species
- Compare to typical/ideal values for {scientific_name}
- Note if it indicates stress, disease, or optimal health
- Give actionable care advice if the value is outside the ideal range

Based on botanical research for {scientific_name}, provide a JSON response with these exact fields:
{{
    "summary": "A 4-6 sentence, highly detailed summary comparing ALL PlantCV metrics above to scientifically documented ideal morphology for {scientific_name}. Reference every metric measured, and explain what each means for this plant's health and care. Be specific: mention actual measured values vs expected values.",
    "recommendations": ["5-7 SPECIFIC care recommendations based on documented {scientific_name} requirements AND the specific PlantCV metrics observed. Reference the actual measurements (e.g., 'With solidity at X.XX, which is lower than typical for {scientific_name}, increase humidity to reduce leaf curling')."],
    "growth_forecast": "Predicted growth for next 2-4 weeks based on documented growth rate for {scientific_name} AND current metrics",
    "issues_detected": ["Health concerns based on PlantCV metrics deviating from documented norms for {scientific_name}. Specifically reference metric values."],
    "care_priority": "HIGH/MEDIUM/LOW - based on how far conditions AND PlantCV metrics deviate from documented species requirements",
    "trend_analysis": "Compare observed growth trends to documented growth rate for {scientific_name}",
    "shape_analysis": "DETAILED interpretation of ALL PlantCV metrics above compared to typical morphology for {scientific_name}. Include specific numeric comparisons and what each means.",
    "metrics_interpretation": {{
        "solidity_assessment": "Is the measured solidity normal for {scientific_name}? What does it indicate about leaf health?",
        "structure_assessment": "Based on leaf tips, branch points, and skeleton path, assess structural development for this species",
        "form_assessment": "Does the eccentricity/aspect ratio/ellipse match typical growth form for {scientific_name}?",
        "color_assessment": "Interpret color histogram, greenness index, and health score for this species",
        "action_items": ["Specific actions based on metrics that deviate from species norms"]
    }},
    "species_parameters": {{
        "ideal_temperature": "Documented temperature range for {scientific_name} (cite source if known)",
        "ideal_humidity": "Documented humidity requirements",
        "light_requirements": "Documented light needs (specify lux/foot-candles if known)",
        "watering_frequency": "Documented watering requirements based on native habitat",
        "growth_rate": "Documented growth rate (cm/year or descriptive)",
        "mature_size": "Documented mature dimensions",
        "soil_type": "Documented soil pH and composition requirements",
        "fertilizer_needs": "Documented nutrient requirements (N-P-K ratios if known)",
        "common_issues": ["2-3 documented common pests/diseases for {scientific_name}"],
        "seasonal_care": "Documented seasonal variations in care (dormancy, flowering periods, etc.)",
        "ideal_solidity": "Expected leaf solidity range for healthy {scientific_name}",
        "typical_form": "Typical growth form (compact/spreading/climbing/rosette) for {scientific_name}"
    }}
}}

STRICT REQUIREMENTS:
- Use the SCIENTIFIC NAME {scientific_name} as the primary reference for all recommendations
- ALWAYS reference the actual PlantCV metrics in your assessment - do not give generic advice
- Compare measured values to species-specific expected values
- Only provide information that is botanically accurate for this species
- Do not guess - if specific data is not available for {scientific_name}, indicate "data not available"
- Reference native habitat conditions when making care recommendations
- Be specific with numeric ranges (temperature, humidity, pH) based on documented requirements
- Distinguish between tropical, subtropical, temperate requirements based on species origin
"""
        
        # Try each API key
        for attempt, api_key in enumerate(self._rotate_keys()):
            try:
                response = requests.post(
                    f"{self.GEMINI_API_URL}?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 4096
                        }
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    
                    # Parse JSON from response
                    parsed = self._parse_ai_response(text)
                    parsed['processing_time_ms'] = (time.time() - start_time) * 1000
                    parsed['method'] = 'gemini'
                    parsed['history_analyzed'] = len(growth_history) if growth_history else 0
                    return parsed
                    
                elif response.status_code in [429, 401]:
                    logger.warning(f"API key {attempt + 1} failed with {response.status_code}")
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API key {attempt + 1} timed out")
                continue
            except Exception as e:
                logger.warning(f"API key {attempt + 1} error: {e}")
                continue
        
        # All keys failed, use template
        return self._generate_template_report(
            species, measurements, previous_measurements, plant_name, start_time, growth_history
        )
    
    def _generate_template_report(
        self,
        species: Optional[SpeciesResult],
        measurements: Optional[MeasurementResult],
        previous_measurements: Optional[MeasurementResult],
        plant_name: str,
        start_time: float,
        growth_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate report using templates with history analysis (fallback)"""
        
        # Determine health status
        health = measurements.health_score if measurements and measurements.success else 50
        greenness = measurements.greenness_index if measurements and measurements.success else 0.5
        
        # Analyze historical trends
        trend_analysis = ""
        avg_health_change = 0
        avg_growth_rate = 0
        
        if growth_history and len(growth_history) >= 2:
            health_scores = [h.get('health_score', 0) for h in growth_history if h.get('health_score')]
            if len(health_scores) >= 2:
                recent_avg = sum(health_scores[:3]) / min(3, len(health_scores))
                older_avg = sum(health_scores[-3:]) / min(3, len(health_scores))
                avg_health_change = recent_avg - older_avg
                
                if avg_health_change > 5:
                    trend_analysis = "Health trending upward over recent measurements. "
                elif avg_health_change < -5:
                    trend_analysis = "Health showing decline over recent measurements. "
                else:
                    trend_analysis = "Health relatively stable over time. "
            
            # Analyze size changes
            areas = [h.get('area_pixels', 0) for h in growth_history if h.get('area_pixels')]
            if len(areas) >= 2 and areas[-1] > 0:
                total_growth = (areas[0] - areas[-1]) / areas[-1] * 100
                avg_growth_rate = total_growth / len(areas)
                trend_analysis += f"Average growth rate: {avg_growth_rate:.1f}% per measurement."
        
        # Generate summary with trend context
        if health >= 80:
            summary = f"Your {plant_name or 'plant'} is thriving with excellent health ({health:.0f}/100). "
            summary += "The foliage shows vibrant coloring and good density. "
        elif health >= 60:
            summary = f"Your {plant_name or 'plant'} is in good condition ({health:.0f}/100). "
            summary += "Some minor attention may help it reach optimal health. "
        elif health >= 40:
            summary = f"Your {plant_name or 'plant'} shows signs of stress ({health:.0f}/100). "
            summary += "Consider reviewing its care routine. "
        else:
            summary = f"Your {plant_name or 'plant'} needs attention ({health:.0f}/100). "
            summary += "Immediate care adjustments recommended. "
        
        if trend_analysis:
            summary += trend_analysis
        
        # Generate recommendations based on history
        recommendations = []
        
        # History-based recommendations
        if growth_history and len(growth_history) >= 2:
            if avg_health_change < -5:
                recommendations.append("PRIORITY: Health has been declining - investigate root causes immediately")
            if avg_growth_rate < 0:
                recommendations.append("Growth has been negative - check for over-pruning, pests, or environmental stress")
            elif avg_growth_rate < 1:
                recommendations.append("Growth rate is slow - consider optimizing light, nutrients, or pot size")
        
        if greenness < 0.5:
            recommendations.append("Increase exposure to indirect sunlight to improve chlorophyll production")
        
        if health < 70:
            recommendations.append("Check soil moisture - both overwatering and underwatering can cause stress")
            recommendations.append("Ensure proper drainage to prevent root issues")
        
        if species and species.care_info:
            if 'watering' in species.care_info:
                recommendations.append(f"Water according to {species.name} needs: {species.care_info.get('watering', 'moderate')}")
        
        if not recommendations:
            recommendations.append("Continue current care routine - plant is doing well")
        
        recommendations.append("Monitor new growth over the next week")
        if health < 70:
            recommendations.append("Consider a balanced fertilizer if growth is slow")
        
        # Growth comparison for issues
        issues = []
        if previous_measurements and measurements:
            prev_area = previous_measurements.area_px if (previous_measurements.area_px is not None and isinstance(previous_measurements.area_px, (int, float))) else 0
            curr_area = measurements.area_px if (measurements.area_px is not None and isinstance(measurements.area_px, (int, float))) else 0
            growth_pct = 0
            if prev_area > 0:
                try:
                    growth_pct = ((curr_area - prev_area) / prev_area * 100)
                except Exception as e:
                    logger.error(f"Growth percentage calculation error: {e}")
                    growth_pct = 0
            if growth_pct < -10:
                issues.append("Plant size has decreased - possible stress or leaf loss")
            elif growth_pct < 2:
                issues.append("Growth appears stagnant - review growing conditions")
        
        if health < 50:
            issues.append("Health score is below optimal - check for pests or disease")
        
        # Historical issues
        if growth_history and len(growth_history) >= 3:
            if avg_health_change < -10:
                issues.append(f"Consistent health decline over {len(growth_history)} measurements")
        
        # Determine priority based on trends
        if avg_health_change < -10:
            priority = 'HIGH'
        elif health < 40 or avg_health_change < -5:
            priority = 'HIGH'
        elif health < 70 or avg_health_change < 0:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'
        
        # Growth forecast based on trend
        if avg_growth_rate > 3:
            forecast = "Based on recent growth patterns, expect continued healthy expansion over the next 2 weeks"
        elif avg_growth_rate > 0:
            forecast = "Steady growth expected to continue. With optimal care, growth may accelerate"
        elif health >= 50:
            forecast = "Focus on maintaining current health. Growth may resume with proper care adjustments"
        else:
            forecast = "Priority is stabilizing plant health. Growth will resume once stress factors are addressed"
        
        return {
            'summary': summary,
            'recommendations': recommendations[:5],
            'growth_forecast': forecast,
            'issues_detected': issues,
            'care_priority': priority,
            'trend_analysis': trend_analysis if trend_analysis else "Insufficient history for trend analysis",
            'processing_time_ms': (time.time() - start_time) * 1000,
            'method': 'template',
            'history_analyzed': len(growth_history) if growth_history else 0
        }
    
    def _build_context(
        self,
        species: Optional[SpeciesResult],
        measurements: Optional[MeasurementResult],
        previous_measurements: Optional[MeasurementResult],
        plant_name: str,
        growth_history: List[Dict[str, Any]] = None
    ) -> str:
        """Build context string for AI prompt including full history"""
        lines = []
        
        if plant_name:
            lines.append(f"Plant Name: {plant_name}")
        
        if species and species.success:
            lines.append(f"Species: {species.name} ({species.scientific_name})")
            lines.append(f"Identification Confidence: {species.confidence:.1%}")
            if species.care_info:
                lines.append(f"Care Info: {json.dumps(species.care_info)}")
        
        lines.append("\n=== CURRENT MEASUREMENTS ===")
        if measurements and measurements.success:
            lines.append(f"Health Score: {measurements.health_score:.1f}/100")
            lines.append(f"Greenness Index: {measurements.greenness_index:.2%}")
            lines.append(f"Estimated Leaves: {measurements.leaf_count_estimate}")
            lines.append(f"Plant Size: {measurements.width_px:.0f}x{measurements.height_px:.0f} px")
            lines.append(f"Area: {measurements.area_px:.0f} px²")
            lines.append(f"Perimeter: {measurements.perimeter_px:.0f} px")
            
            if measurements.height_cm:
                lines.append(f"Estimated Real Size: {measurements.width_cm:.1f}x{measurements.height_cm:.1f} cm")
                if measurements.area_cm2:
                    lines.append(f"Estimated Area: {measurements.area_cm2:.1f} cm²")
            
            # Include advanced PlantCV metrics
            if measurements.advanced_metrics:
                am = measurements.advanced_metrics
                lines.append("\n=== DETAILED SHAPE ANALYSIS (PlantCV) ===")
                
                # Shape metrics
                if am.get('solidity'):
                    lines.append(f"Solidity: {am['solidity']:.3f} (1.0 = perfectly compact, lower = more irregular/damaged)")
                if am.get('aspect_ratio'):
                    lines.append(f"Aspect Ratio: {am['aspect_ratio']:.2f} (width/height)")
                if am.get('convex_hull_area'):
                    lines.append(f"Convex Hull Area: {am['convex_hull_area']:.0f} px²")
                
                # Ellipse-based measurements (better for plant shape)
                if am.get('ellipse_major_axis') or am.get('ellipse_minor_axis'):
                    lines.append(f"Fitted Ellipse: {am.get('ellipse_major_axis', 0):.1f} x {am.get('ellipse_minor_axis', 0):.1f} px")
                    if am.get('ellipse_eccentricity'):
                        lines.append(f"Eccentricity: {am['ellipse_eccentricity']:.3f} (0 = circular, 1 = elongated)")
                    if am.get('ellipse_angle'):
                        lines.append(f"Plant Orientation: {am['ellipse_angle']:.1f}° from horizontal")
                
                # Morphology/structure
                if am.get('leaf_tips_detected'):
                    lines.append(f"Leaf Tips Detected: {am['leaf_tips_detected']}")
                if am.get('branch_points'):
                    lines.append(f"Branch Points: {am['branch_points']}")
                if am.get('longest_path'):
                    lines.append(f"Longest Skeleton Path: {am['longest_path']:.0f} px")
                
                # Coverage
                if am.get('mask_coverage_pct'):
                    lines.append(f"Image Coverage: {am['mask_coverage_pct']:.1f}% of frame")
            
            # Color distribution for health analysis
            if measurements.color_histogram:
                ch = measurements.color_histogram
                lines.append("\n=== COLOR DISTRIBUTION ===")
                if 'green' in ch:
                    lines.append(f"Green channel: mean={ch['green'].get('mean', 0):.1f}, std={ch['green'].get('std', 0):.1f}")
                if 'red' in ch:
                    lines.append(f"Red channel: mean={ch['red'].get('mean', 0):.1f}, std={ch['red'].get('std', 0):.1f}")
                if 'blue' in ch:
                    lines.append(f"Blue channel: mean={ch['blue'].get('mean', 0):.1f}, std={ch['blue'].get('std', 0):.1f}")
                # Interpretation hints
                lines.append("(Higher green = healthier; High red/yellow may indicate stress or disease)")
        
        if previous_measurements and measurements:
            lines.append("\n=== CHANGE SINCE LAST MEASUREMENT ===")
            prev_area = previous_measurements.area_px if (previous_measurements.area_px is not None and isinstance(previous_measurements.area_px, (int, float))) else 0
            curr_area = measurements.area_px if (measurements.area_px is not None and isinstance(measurements.area_px, (int, float))) else 0
            if prev_area > 0:
                try:
                    growth = (curr_area - prev_area) / prev_area * 100
                except Exception as e:
                    logger.error(f"Growth calculation error: {e}")
                    growth = 0
                lines.append(f"Size Change: {growth:+.1f}%")
            if previous_measurements.health_score is not None and measurements.health_score is not None:
                try:
                    health_change = measurements.health_score - previous_measurements.health_score
                except Exception as e:
                    logger.error(f"Health change calculation error: {e}")
                    health_change = 0
                lines.append(f"Health Change: {health_change:+.1f} points")
        
        # Add full growth history
        if growth_history and len(growth_history) > 0:
            lines.append(f"\n=== GROWTH HISTORY ({len(growth_history)} records) ===")
            for i, record in enumerate(growth_history[:10]):  # Limit to last 10 records
                date = record.get('recorded_at', 'Unknown date')
                health = record.get('health_score', 'N/A')
                height = record.get('height_pixels', 'N/A')
                width = record.get('width_pixels', 'N/A')
                area = record.get('area_pixels', 'N/A')
                leaves = record.get('estimated_leaf_count', 'N/A')
                lines.append(f"  {i+1}. {date}: Health={health}, Size={width}x{height}px, Area={area}px², Leaves={leaves}")
            
            # Calculate and add trend summary
            health_scores = [h.get('health_score', 0) for h in growth_history if h.get('health_score')]
            if health_scores:
                avg_health = sum(health_scores) / len(health_scores)
                min_health = min(health_scores)
                max_health = max(health_scores)
                lines.append(f"\nHealth Summary: Avg={avg_health:.1f}, Min={min_health:.1f}, Max={max_health:.1f}")
            
            areas = [h.get('area_pixels', 0) for h in growth_history if h.get('area_pixels')]
            if areas and len(areas) >= 2:
                total_growth = (areas[0] - areas[-1]) / areas[-1] * 100 if areas[-1] > 0 else 0
                lines.append(f"Total Size Change: {total_growth:+.1f}% over {len(areas)} measurements")
        
        return "\n".join(lines)
    
    def _parse_ai_response(self, text: str) -> Dict[str, Any]:
        """Parse AI response, handling JSON embedded in text"""
        import re
        
        # Clean up common markdown issues
        cleaned = text.strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        try:
            # Try direct JSON parse
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from text
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                # Try to repair truncated JSON by closing brackets
                partial = json_match.group()
                # Count open/close brackets
                open_braces = partial.count('{') - partial.count('}')
                open_brackets = partial.count('[') - partial.count(']')
                
                # Add missing closing brackets/braces
                repaired = partial
                if not repaired.rstrip().endswith('"') and '"' in repaired:
                    # Truncated in middle of string - close it
                    repaired = repaired.rstrip() + '"'
                repaired += ']' * open_brackets
                repaired += '}' * open_braces
                
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass
        
        # Extract individual fields from truncated response
        result = {
            'summary': '',
            'recommendations': [],
            'growth_forecast': '',
            'issues_detected': [],
            'care_priority': 'MEDIUM',
            'species_parameters': {},
            'metrics_interpretation': {}
        }
        
        # Try to extract summary
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned)
        if summary_match:
            result['summary'] = summary_match.group(1).replace('\\"', '"').replace('\\n', ' ')
        else:
            # Fallback: use all text
            result['summary'] = cleaned[:800] if cleaned else "Analysis completed"
        
        # Extract recommendations array
        rec_match = re.search(r'"recommendations"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        if rec_match:
            recs = re.findall(r'"([^"]+)"', rec_match.group(1))
            result['recommendations'] = [r.replace('\\"', '"') for r in recs[:5]]
        
        # Extract growth_forecast
        forecast_match = re.search(r'"growth_forecast"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned)
        if forecast_match:
            result['growth_forecast'] = forecast_match.group(1).replace('\\"', '"')
        
        # Extract issues_detected
        issues_match = re.search(r'"issues_detected"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        if issues_match:
            issues = re.findall(r'"([^"]+)"', issues_match.group(1))
            result['issues_detected'] = [i.replace('\\"', '"') for i in issues[:5]]
        
        # Extract care_priority
        priority_match = re.search(r'"care_priority"\s*:\s*"([^"]+)"', cleaned)
        if priority_match:
            result['care_priority'] = priority_match.group(1)
        
        # Extract shape_analysis
        shape_match = re.search(r'"shape_analysis"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned)
        if shape_match:
            result['shape_analysis'] = shape_match.group(1).replace('\\"', '"')
        
        # Extract trend_analysis
        trend_match = re.search(r'"trend_analysis"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned)
        if trend_match:
            result['trend_analysis'] = trend_match.group(1).replace('\\"', '"')

        # Extract metrics_interpretation (as JSON object)
        metrics_match = re.search(r'"metrics_interpretation"\s*:\s*(\{[\s\S]*?\})', cleaned)
        if metrics_match:
            try:
                result['metrics_interpretation'] = json.loads(metrics_match.group(1))
            except Exception:
                pass

        # Extract species_parameters (as JSON object)
        species_params_match = re.search(r'"species_parameters"\s*:\s*(\{[\s\S]*?\})', cleaned)
        if species_params_match:
            try:
                result['species_parameters'] = json.loads(species_params_match.group(1))
            except Exception:
                pass

        # Extract metrics_interpretation (as JSON object or string)
        metrics_match = re.search(r'"metrics_interpretation"\s*:\s*(\{.*?\}|"[^"]*")', cleaned, re.DOTALL)
        if metrics_match:
            metrics_str = metrics_match.group(1)
            try:
                if metrics_str.startswith('{'):
                    result['metrics_interpretation'] = json.loads(metrics_str)
                else:
                    # If it's a string, just store as a string
                    result['metrics_interpretation'] = metrics_str.strip('"')
            except Exception:
                result['metrics_interpretation'] = metrics_str

        # Extract species_parameters (as JSON object or string)
        species_params_match = re.search(r'"species_parameters"\s*:\s*(\{.*?\}|"[^"]*")', cleaned, re.DOTALL)
        if species_params_match:
            species_params_str = species_params_match.group(1)
            try:
                if species_params_str.startswith('{'):
                    result['species_parameters'] = json.loads(species_params_str)
                else:
                    result['species_parameters'] = species_params_str.strip('"')
            except Exception:
                result['species_parameters'] = species_params_str
        
        return result
    
    def _rotate_keys(self):
        """Yield API keys in rotation"""
        for i in range(len(self.api_keys)):
            idx = (self._current_key_idx + i) % len(self.api_keys)
            yield self.api_keys[idx]
        self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)


# ============================================================================
# PLANT.ID INTEGRATION (Species Identification)
# ============================================================================

class PlantIDClient:
    """
    Plant.id API client for species identification.
    Wraps the existing plantid_service with unified interface.
    """
    
    def __init__(self, api_keys: List[str] = None):
        """Initialize Plant.id client with key rotation"""
        # Prefer new env var for key rotation, fallback to legacy keys
        keys = api_keys or os.getenv('PLANTID_API_KEYS', '').split(',')
        keys = [k.strip() for k in keys if k.strip()]
        if not keys:
            # Fallback to legacy single/backup keys
            legacy = [os.getenv('PLANTID_API_KEY', ''), os.getenv('PLANTID_API_KEY_BACKUP', '')]
            keys = [k.strip() for k in legacy if k.strip()]
        self.api_keys = keys
        self._current_key_idx = 0
        self.api_url = os.getenv('PLANTID_API_URL', 'https://api.plant.id/v3')
        logger.info(f"PlantIDClient initialized with {len(self.api_keys)} API keys")
    
    def _rotate_keys(self):
        """Yield API keys in rotation (round-robin)"""
        for i in range(len(self.api_keys)):
            idx = (self._current_key_idx + i) % len(self.api_keys)
            yield self.api_keys[idx]
        self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)

    def identify(self, image: np.ndarray) -> SpeciesResult:
        """
        Identify plant species from image using rotating API keys.
        """
        start_time = time.time()
        if not self.api_keys:
            return SpeciesResult(
                success=False,
                error="Plant.id API keys not configured",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        try:
            import requests
            # Encode image
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            # Try each API key in rotation
            for api_key in self._rotate_keys():
                if not api_key:
                    continue
                response = requests.post(
                    f"{self.api_url}/identification",
                    headers={
                        'Content-Type': 'application/json',
                        'Api-Key': api_key
                    },
                    json={
                        'images': [image_base64]
                    },
                    timeout=30
                )
                logger.info(f"Plant.id response status: {response.status_code}")
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.debug(f"Plant.id raw response: {data}")
                    return self._parse_response(data, start_time)
                elif response.status_code in [401, 429]:
                    logger.warning(f"Plant.id API key issue: {response.status_code}, trying next key")
                    continue  # Try next key
                else:
                    logger.warning(f"Plant.id unexpected status: {response.status_code} - {response.text[:200]}")
            return SpeciesResult(
                success=False,
                error="All Plant.id API keys exhausted",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Plant.id error: {e}")
            return SpeciesResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _parse_response(self, data: dict, start_time: float) -> SpeciesResult:
        """Parse Plant.id API response"""
        try:
            suggestions = data.get('result', {}).get('classification', {}).get('suggestions', [])
            
            if not suggestions:
                return SpeciesResult(
                    success=False,
                    error="No species identified",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            top = suggestions[0]
            
            return SpeciesResult(
                success=True,
                name=top.get('name', 'Unknown'),
                scientific_name=top.get('name', 'Unknown'),  # Plant.id returns scientific name
                confidence=top.get('probability', 0),
                common_names=top.get('details', {}).get('common_names', []),
                care_info={
                    'watering': top.get('details', {}).get('watering', {}).get('max', 'moderate'),
                    'sunlight': top.get('details', {}).get('best_light_condition', 'partial'),
                    'propagation': top.get('details', {}).get('propagation_methods', [])
                },
                description=top.get('details', {}).get('description', {}).get('value', ''),
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return SpeciesResult(
                success=False,
                error=f"Parse error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000
            )


# ============================================================================
# UNIFIED GROWTH TRACKER (Main Interface)
# ============================================================================

class PlantGrowthTracker:
    """
    Unified plant growth tracking system.
    
    Efficiently orchestrates:
    - Rembg segmentation
    - PlantCV measurements  
    - Plant.id species identification
    - Gemini AI report generation
    """
    
    def __init__(
        self,
        pixels_per_cm: float = None,
        enable_species_id: bool = True,
        enable_ai_reports: bool = True,
        rembg_model: str = "u2net"
    ):
        """
        Initialize the growth tracker.
        
        Args:
            pixels_per_cm: Scale factor for real measurements (None = pixel-only)
            enable_species_id: Whether to identify species via Plant.id
            enable_ai_reports: Whether to generate AI reports via Gemini
            rembg_model: Rembg model to use
        """
        # Initialize components (lazy loading)
        self._segmenter = RembgSegmenter(model_name=rembg_model)
        self._analyzer = PlantCVAnalyzer(pixels_per_cm=pixels_per_cm)
        self._species_client = PlantIDClient() if enable_species_id else None
        self._reporter = GeminiReporter() if enable_ai_reports else None
        
        self._enable_species = enable_species_id
        self._enable_ai = enable_ai_reports
        
        # Result cache
        self._cache: Dict[str, GrowthReport] = {}
        
        logger.info(f"PlantGrowthTracker initialized (species={enable_species_id}, ai={enable_ai_reports})")
    
    def analyze(
        self,
        image: Union[np.ndarray, bytes, str],
        previous_report: Optional[GrowthReport] = None,
        plant_name: str = None,
        skip_species: bool = False,
        skip_ai: bool = False,
        growth_history: List[Dict[str, Any]] = None,
        expected_species: str = None,
        estimate_real_size: bool = True
    ) -> GrowthReport:
        """
        Perform complete plant growth analysis with history context.
        
        Args:
            image: Input image (numpy array, bytes, or base64 string)
            previous_report: Previous analysis for comparison
            plant_name: Optional custom plant name
            skip_species: Skip species identification this time
            skip_ai: Skip AI report generation this time
            growth_history: List of past measurements for trend analysis
            expected_species: Expected plant species for verification
            estimate_real_size: Whether to estimate real cm measurements
            
        Returns:
            GrowthReport with complete analysis
        """
        total_start = time.time()
        warnings = []
        components_used = []
        species_verified = True
        species_mismatch_reason = None
        
        try:
            # Load image
            img = self._load_image(image)
            if img is None:
                return GrowthReport(
                    success=False,
                    error="Failed to load image",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            # Generate image hash for caching
            image_hash = hashlib.md5(img.tobytes()).hexdigest()[:16]
            
            # ============================================================
            # STEP 1: SPECIES VERIFICATION (MUST PASS BEFORE ANALYSIS)
            # ============================================================
            species_result = None
            if self._enable_species and self._species_client:
                logger.info("Step 1: Running Plant.id species identification...")
                species_result = self._species_client.identify(img)
                components_used.append("plant.id")
                
                if not species_result.success:
                    logger.warning(f"Plant.id failed: {species_result.error}")
                    warnings.append(f"Species ID warning: {species_result.error}")
                else:
                    logger.info(f"Plant.id identified: {species_result.name} (confidence: {species_result.confidence:.1%})")
                    
                    # If expected species provided, VERIFY BEFORE PROCEEDING
                    if expected_species:
                        species_verified, species_mismatch_reason = self._verify_species(
                            species_result, expected_species
                        )
                        
                        if not species_verified:
                            # STOP HERE - Return error asking for correct plant photo
                            logger.warning(f"Species mismatch! Expected: {expected_species}, Got: {species_result.name}")
                            return GrowthReport(
                                success=False,
                                error=f"Wrong plant detected! Please take a photo of your {expected_species}.",
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                image_hash=image_hash,
                                species=species_result,
                                species_verified=False,
                                species_mismatch_reason=species_mismatch_reason,
                                total_processing_time_ms=(time.time() - total_start) * 1000,
                                components_used=components_used,
                                warnings=[f"Detected: {species_result.name} ({species_result.confidence:.0%} confidence). Expected: {expected_species}"]
                            )
                        else:
                            logger.info(f"Species verified: {species_result.name} matches expected {expected_species}")
            
            # ============================================================
            # STEP 2: SEGMENTATION (only if species verified)
            # ============================================================
            seg_result = self._segmenter.segment(img)
            components_used.append("rembg" if seg_result.method == "rembg" else "color_segmentation")
            
            if not seg_result.success:
                warnings.append(f"Segmentation warning: {seg_result.error}")
                seg_result.mask = np.ones(img.shape[:2], dtype=np.uint8)
            
            # Step 3: Measurements
            measure_result = self._analyzer.measure(img, seg_result.mask)
            components_used.append("plantcv" if self._analyzer.plantcv_available else "opencv")
            
            if not measure_result.success:
                warnings.append(f"Measurement warning: {measure_result.error}")
            
            # Step 3.5: Estimate real-world measurements if requested
            if estimate_real_size and measure_result.success:
                measure_result = self._estimate_real_measurements(img, measure_result, seg_result.mask)
            
            # Step 4: AI Report with history context
            ai_report = {}
            if self._enable_ai and not skip_ai and self._reporter:
                previous_measurements = previous_report.measurements if previous_report else None
                ai_report = self._reporter.generate_report(
                    species=species_result,
                    measurements=measure_result,
                    previous_measurements=previous_measurements,
                    plant_name=plant_name or (species_result.name if species_result and species_result.success else None),
                    growth_history=growth_history
                )
                components_used.append("gemini" if ai_report.get('method') == 'gemini' else "template")
            
            # Step 5: Calculate growth delta if previous report exists
            growth_delta = {}
            if previous_report and previous_report.measurements and measure_result.success:
                prev = previous_report.measurements
                curr = measure_result
                
                # Calculate time elapsed
                days_elapsed = self._calculate_days_elapsed(previous_report.timestamp)
                
                # Core size changes
                prev_area = prev.area_px if prev.area_px is not None else 0
                curr_area = curr.area_px if curr.area_px is not None else 0
                prev_height = prev.height_px if prev.height_px is not None else 0
                curr_height = curr.height_px if curr.height_px is not None else 0
                prev_width = prev.width_px if prev.width_px is not None else 0
                curr_width = curr.width_px if curr.width_px is not None else 0
                prev_health = prev.health_score if prev.health_score is not None else 0
                curr_health = curr.health_score if curr.health_score is not None else 0
                prev_green = prev.greenness_index if prev.greenness_index is not None else 0
                curr_green = curr.greenness_index if curr.greenness_index is not None else 0
                prev_leaf = prev.leaf_count_estimate if prev.leaf_count_estimate is not None else 0
                curr_leaf = curr.leaf_count_estimate if curr.leaf_count_estimate is not None else 0
                prev_height_cm = prev.height_cm if prev.height_cm is not None else None
                curr_height_cm = curr.height_cm if curr.height_cm is not None else None
                prev_width_cm = prev.width_cm if prev.width_cm is not None else None
                curr_width_cm = curr.width_cm if curr.width_cm is not None else None

                area_change_pct = ((curr_area - prev_area) / prev_area * 100) if prev_area and prev_area > 0 else 0
                height_change_pct = ((curr_height - prev_height) / prev_height * 100) if prev_height and prev_height > 0 else 0
                width_change_pct = ((curr_width - prev_width) / prev_width * 100) if prev_width and prev_width > 0 else 0

                growth_delta = {
                    # Size changes
                    'area_change_pct': round(area_change_pct, 1),
                    'height_change_pct': round(height_change_pct, 1),
                    'width_change_pct': round(width_change_pct, 1),

                    # Health changes
                    'health_change': round(curr_health - prev_health, 1),
                    'greenness_change': round((curr_green - prev_green) * 100, 1),

                    # Leaf/structure changes
                    'leaf_change': curr_leaf - prev_leaf,

                    # Time context
                    'days_elapsed': days_elapsed,
                    'hours_elapsed': days_elapsed * 24 if days_elapsed < 1 else None,

                    # Previous values for comparison display
                    'previous': {
                        'health_score': round(prev_health, 1),
                        'greenness_index': round(prev_green * 100, 1),
                        'leaf_count': prev_leaf,
                        'area_px': int(prev_area),
                        'height_px': int(prev_height),
                        'width_px': int(prev_width),
                        'height_cm': round(prev_height_cm, 1) if prev_height_cm is not None else None,
                        'width_cm': round(prev_width_cm, 1) if prev_width_cm is not None else None
                    },

                    # Current values
                    'current': {
                        'health_score': round(curr_health, 1),
                        'greenness_index': round(curr_green * 100, 1),
                        'leaf_count': curr_leaf,
                        'area_px': int(curr_area),
                        'height_px': int(curr_height),
                        'width_px': int(curr_width),
                        'height_cm': round(curr_height_cm, 1) if curr_height_cm is not None else None,
                        'width_cm': round(curr_width_cm, 1) if curr_width_cm is not None else None
                    },

                    # Growth rate (per day)
                    'growth_rate_per_day': round(area_change_pct / max(days_elapsed, 0.1), 2) if days_elapsed > 0 else None,

                    # Overall assessment
                    'trend': 'growing' if area_change_pct > 2 else 'declining' if area_change_pct < -2 else 'stable',
                    'health_trend': 'improving' if (curr_health - prev_health) > 3 else 'declining' if (curr_health - prev_health) < -3 else 'stable'
                }
                
                # Add advanced metrics comparison if available
                if curr.advanced_metrics and prev.advanced_metrics:
                    prev_am = prev.advanced_metrics
                    curr_am = curr.advanced_metrics
                    growth_delta['solidity_change'] = round((curr_am.get('solidity', 0) - prev_am.get('solidity', 0)) * 100, 1)
                    growth_delta['leaf_tips_change'] = (curr_am.get('leaf_tips_detected', 0) or 0) - (prev_am.get('leaf_tips_detected', 0) or 0)
                    growth_delta['branch_change'] = (curr_am.get('branch_points', 0) or 0) - (prev_am.get('branch_points', 0) or 0)
            
            # Build final report
            # Build plant diary/history
            plant_diary = []
            if growth_history:
                for record in growth_history:
                    diary_entry = {
                        'timestamp': record.get('recorded_at') or record.get('timestamp'),
                        'image': record.get('image') or record.get('image_path') or None,
                        'health_score': record.get('health_score'),
                        'greenness_index': record.get('greenness_index'),
                        'leaf_count_estimate': record.get('estimated_leaf_count') or record.get('leaf_count_estimate'),
                        'area_px': record.get('area_pixels') or record.get('area_px'),
                        'height_px': record.get('height_pixels') or record.get('height_px'),
                        'width_px': record.get('width_pixels') or record.get('width_px'),
                        'advanced_metrics': record.get('advanced_metrics', {}),
                        'notes': record.get('notes', "")
                    }
                    plant_diary.append(diary_entry)
            report = GrowthReport(
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                image_hash=image_hash,
                segmentation=seg_result,
                measurements=measure_result,
                species=species_result,
                species_verified=species_verified,
                species_mismatch_reason=species_mismatch_reason,
                health_summary=ai_report.get('health_summary', ''),
                care_recommendations=ai_report.get('care_recommendations', []),
                growth_forecast=ai_report.get('growth_forecast', ''),
                issues_detected=ai_report.get('issues_detected', []),
                growth_trend_analysis=ai_report.get('growth_trend_analysis', ''),
                shape_and_structure_analysis=ai_report.get('shape_and_structure_analysis', ''),
                metrics_interpretation=ai_report.get('metrics_interpretation', {}),
                species_care_profile=ai_report.get('species_care_profile', {}),
                # Gemini AI fields
                ai_summary=ai_report.get('summary'),
                ai_recommendations=ai_report.get('recommendations'),
                ai_growth_forecast=ai_report.get('growth_forecast'),
                ai_issues_detected=ai_report.get('issues_detected'),
                ai_trend_analysis=ai_report.get('trend_analysis'),
                ai_shape_analysis=ai_report.get('shape_analysis'),
                ai_metrics_interpretation=ai_report.get('metrics_interpretation', {}),
                species_parameters=ai_report.get('species_parameters', {}),
                growth_delta=growth_delta,
                plant_diary=plant_diary,
                history_record_count=len(growth_history) if growth_history else 0,
                total_processing_time_ms=(time.time() - total_start) * 1000,
                components_used=components_used,
                warnings=warnings
            )
            
            # Cache result
            self._cache[image_hash] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return GrowthReport(
                success=False,
                error=str(e),
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_processing_time_ms=(time.time() - total_start) * 1000
            )
    
    def _load_image(self, image: Union[np.ndarray, bytes, str]) -> Optional[np.ndarray]:
        """Load image from various sources"""
        try:
            if isinstance(image, np.ndarray):
                return image
            
            if isinstance(image, bytes):
                nparr = np.frombuffer(image, np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if isinstance(image, str):
                # Check if base64
                if image.startswith('data:'):
                    image = image.split(',')[1]
                
                try:
                    decoded = base64.b64decode(image)
                    nparr = np.frombuffer(decoded, np.uint8)
                    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                except Exception:
                    # Assume file path
                    return cv2.imread(image)
            
            return None
            
        except Exception as e:
            logger.error(f"Image load error: {e}")
            return None
    
    def _calculate_days_elapsed(self, previous_timestamp: str) -> float:
        """Calculate days since previous analysis"""
        try:
            prev_dt = datetime.fromisoformat(previous_timestamp.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = now - prev_dt
            return delta.total_seconds() / 86400
        except Exception:
            return 0
    
    def _verify_species(
        self, 
        species_result: SpeciesResult, 
        expected_species: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that identified species matches expected plant.
        
        Args:
            species_result: Result from Plant.id
            expected_species: Expected scientific name from garden database
            
        Returns:
            Tuple of (verified: bool, mismatch_reason: str or None)
        """
        # If no expected species provided, skip verification
        if not expected_species:
            logger.warning("No scientific name in garden record - skipping verification")
            return True, None
        
        # If Plant.id failed or couldn't identify - REJECT (not a valid plant image)
        if not species_result or not species_result.success:
            return False, "Could not identify any plant in this image. Please upload a clear photo of your plant."
        
        # Minimum confidence threshold - reject low confidence
        if species_result.confidence < 0.4:
            return False, f"Image unclear or not a recognizable plant (confidence: {species_result.confidence:.0%}). Please upload a clearer photo."
        
        # Get scientific names (lowercase for comparison)
        expected_scientific_raw = expected_species
        identified_scientific_raw = species_result.scientific_name if species_result.scientific_name else ""
        expected_scientific = expected_scientific_raw.lower().strip()
        identified_scientific = identified_scientific_raw.lower().strip()

        logger.info("[SCINAME DEBUG] --- Scientific Name Comparison ---")
        logger.info(f"[SCINAME DEBUG] From Plant Card (frontend): '{expected_scientific_raw}' (normalized: '{expected_scientific}')")
        logger.info(f"[SCINAME DEBUG] From Uploaded Image (Plant.id): '{identified_scientific_raw}' (normalized: '{identified_scientific}')")
        logger.info(f"[SCINAME DEBUG] Comparing: frontend='{expected_scientific}' vs detected='{identified_scientific}'")

        # Strict scientific name comparison (exact match only)
        if not identified_scientific:
            logger.warning("[SCINAME DEBUG] No scientific name detected from image.")
            return False, f"Plant.id could not determine scientific name. Identified as '{species_result.name}' with {species_result.confidence:.0%} confidence."
        if expected_scientific == identified_scientific:
            logger.info("[SCINAME DEBUG] Scientific names match. Proceeding with analysis.")
            return True, None
        # Scientific name mismatch - reject (no partial or genus/species fallback)
        logger.warning(f"[SCINAME DEBUG] Scientific name mismatch: frontend='{expected_scientific_raw}' vs detected='{identified_scientific_raw}'")
        reason = f"Scientific name mismatch: expected '{expected_species}' but identified '{species_result.scientific_name}' ({species_result.name}) with {species_result.confidence:.0%} confidence"
        return False, reason
    
    def _estimate_real_measurements(
        self,
        image: np.ndarray,
        measurements: MeasurementResult,
        mask: np.ndarray
    ) -> MeasurementResult:
        """
        Estimate real-world measurements (in cm) from pixel measurements.
        
        Uses heuristics based on:
        - Typical pot sizes
        - Plant-to-image ratio
        - Common plant sizes
        
        Args:
            image: Original image
            measurements: Current pixel measurements
            mask: Segmentation mask
            
        Returns:
            MeasurementResult with added height_cm, width_cm, area_cm2
        """
        if not measurements.success:
            return measurements
        
        img_height, img_width = image.shape[:2]
        plant_height = measurements.height_px
        plant_width = measurements.width_px
        
        # Calculate plant coverage ratio
        # coverage_ratio removed (unused)
        
        # Heuristic: Estimate pixels per cm based on image size and coverage
        # Assumes typical smartphone photo of potted plant
        # - Small pot (10-15cm): Plant usually fills 30-60% of frame
        # - Medium pot (15-25cm): Plant usually fills 40-70% of frame
        # - Large pot (25-40cm): Plant fills 50-80% of frame
        
        # Estimate based on typical scenarios
        plant_height_ratio = plant_height / img_height
        
        if plant_height_ratio < 0.3:
            # Small plant or zoomed out photo
            # Assume image captures ~50cm height
            estimated_cm_per_pixel = 50.0 / img_height
        elif plant_height_ratio < 0.5:
            # Medium plant
            # Assume image captures ~40cm height
            estimated_cm_per_pixel = 40.0 / img_height
        elif plant_height_ratio < 0.7:
            # Large plant filling most of frame
            # Assume image captures ~30cm height
            estimated_cm_per_pixel = 30.0 / img_height
        else:
            # Close-up shot
            # Assume image captures ~20cm height
            estimated_cm_per_pixel = 20.0 / img_height
        
        # Calculate real measurements
        measurements.height_cm = round(plant_height * estimated_cm_per_pixel, 1)
        measurements.width_cm = round(plant_width * estimated_cm_per_pixel, 1)
        measurements.area_cm2 = round(measurements.area_px * (estimated_cm_per_pixel ** 2), 1)
        
        # Store the calibration factor used
        if measurements.advanced_metrics:
            measurements.advanced_metrics['estimated_pixels_per_cm'] = round(1 / estimated_cm_per_pixel, 2)
            measurements.advanced_metrics['measurement_method'] = 'heuristic_estimate'
        
        logger.info(f"Estimated real size: {measurements.width_cm}x{measurements.height_cm} cm")
        
        return measurements
    
    def get_visualization(
        self,
        image: np.ndarray,
        report: GrowthReport,
        show_mask: bool = True,
        show_measurements: bool = True,
        show_health: bool = True
    ) -> np.ndarray:
        """
        Generate annotated visualization of analysis.
        
        Args:
            image: Original image
            report: Analysis report
            show_mask: Overlay segmentation mask
            show_measurements: Add measurement annotations
            show_health: Add health indicator
            
        Returns:
            Annotated image
        """
        vis = image.copy()
        
        if show_mask and report.segmentation and report.segmentation.mask is not None:
            # Create colored overlay
            mask = report.segmentation.mask
            overlay = np.zeros_like(vis)
            overlay[:, :, 1] = mask * 100  # Green tint
            vis = cv2.addWeighted(vis, 0.8, overlay, 0.2, 0)
            
            # Draw contour
            contours, _ = cv2.findContours(
                (mask * 255).astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(vis, contours, -1, (0, 255, 0), 2)
        
        if show_measurements and report.measurements and report.measurements.success:
            m = report.measurements
            bbox = m.advanced_metrics.get('bounding_box', {})
            
            if bbox:
                x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
                
                # Draw bounding box
                cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 255, 0), 2)
                
                # Add dimension labels
                cv2.putText(vis, f"{w}px", (x + w//2 - 20, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                cv2.putText(vis, f"{h}px", (x + w + 5, y + h//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        if show_health and report.measurements and report.measurements.success:
            health = report.measurements.health_score
            
            # Health bar
            bar_width = 100
            bar_height = 15
            bar_x, bar_y = 10, 10
            
            # Background
            cv2.rectangle(vis, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
            
            # Health fill
            fill_width = int(bar_width * health / 100)
            color = (0, 255, 0) if health >= 70 else (0, 255, 255) if health >= 40 else (0, 0, 255)
            cv2.rectangle(vis, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), color, -1)
            
            # Label
            cv2.putText(vis, f"Health: {health:.0f}%", (bar_x, bar_y + bar_height + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return vis
    
    def to_dict(self, report: GrowthReport) -> Dict[str, Any]:
        """Convert report to JSON-serializable dictionary"""
        def convert(obj):
            if hasattr(obj, '__dict__'):
                d = {}
                for k, v in obj.__dict__.items():
                    if isinstance(v, np.ndarray):
                        continue  # Skip numpy arrays
                    d[k] = convert(v)
                return d
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj
        return convert(report)
    
    def clear_cache(self):
        """Clear the result cache"""
        self._cache.clear()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_plant(
    image: Union[np.ndarray, bytes, str],
    pixels_per_cm: float = None,
    plant_name: str = None,
    full_analysis: bool = True
) -> Dict[str, Any]:
    """
    Quick analysis function - one-shot plant analysis.
    
    Args:
        image: Plant image (numpy array, bytes, or base64)
        pixels_per_cm: Scale factor for real measurements
        plant_name: Optional plant name
        full_analysis: Whether to run all components
        
    Returns:
        Dictionary with analysis results
    """
    tracker = PlantGrowthTracker(
        pixels_per_cm=pixels_per_cm,
        enable_species_id=full_analysis,
        enable_ai_reports=full_analysis
    )
    
    report = tracker.analyze(image, plant_name=plant_name)
    return tracker.to_dict(report)


def quick_health_check(image: Union[np.ndarray, bytes, str]) -> Dict[str, Any]:
    """
    Quick health check - fast analysis without API calls.
    
    Args:
        image: Plant image
        
    Returns:
        Dictionary with health metrics
    """
    tracker = PlantGrowthTracker(
        enable_species_id=False,
        enable_ai_reports=False
    )
    
    report = tracker.analyze(image, skip_species=True, skip_ai=True)
    
    if report.success and report.measurements:
        return {
            'success': True,
            'health_score': report.measurements.health_score,
            'greenness': report.measurements.greenness_index,
            'leaf_count': report.measurements.leaf_count_estimate,
            'processing_time_ms': report.total_processing_time_ms
        }
    
    return {'success': False, 'error': report.error}


# ============================================================================
# MAIN (Testing)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Plant Growth Tracker - System Check")
    print("=" * 60)
    
    # Check components
    tracker = PlantGrowthTracker(
        enable_species_id=True,
        enable_ai_reports=True
    )
    
    print(f"\n✅ Rembg available: {tracker._segmenter.rembg_available}")
    print(f"✅ PlantCV available: {tracker._analyzer.plantcv_available}")
    print(f"✅ Plant.id configured: {bool(tracker._species_client and tracker._species_client.api_key)}")
    print(f"✅ Gemini configured: {bool(tracker._reporter and tracker._reporter.api_keys)}")
    
    print("\n" + "=" * 60)
    print("Ready for plant analysis!")
    print("=" * 60)
