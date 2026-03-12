"""
Comprehensive Plant Measurement System
SAM + OpenCV for complete plant feature extraction and growth tracking

Features:
- Reference scale detection and calibration
- Core geometry (area, height, width, perimeter)
- Growth tracking (time-series comparisons)
- Plant-type specific metrics
- Leaf features
- Color/health metrics
- Structural complexity
- Spatial expansion metrics
- Advanced features (skeletonization, fractal complexity)
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from scipy import ndimage
from skimage import morphology
import math


@dataclass
class ScaleCalibration:
    """Store scale calibration data"""
    pixels_per_mm: float
    reference_type: str
    reference_pixels: int
    real_size_mm: float
    confidence: float


class ReferenceScaleDetector:
    """
    Detect reference objects for scale calibration.
    Supports: coins, rulers, calibration cards, pot diameter
    """
    
    # Common reference object sizes in mm
    REFERENCE_OBJECTS = {
        # US Coins
        'us_quarter': 24.26,
        'us_penny': 19.05,
        'us_nickel': 21.21,
        'us_dime': 17.91,
        # Other coins
        'euro_1': 23.25,
        'euro_2': 25.75,
        'uk_pound': 22.5,
        # Cards
        'credit_card_width': 85.6,
        'credit_card_height': 53.98,
        # Common pot sizes (diameter)
        'pot_4inch': 101.6,
        'pot_6inch': 152.4,
        'pot_8inch': 203.2,
    }
    
    def __init__(self):
        self.last_calibration: Optional[ScaleCalibration] = None
    
    def detect_circular_reference(self, image: np.ndarray, 
                                   plant_mask: np.ndarray) -> Dict[str, Any]:
        """Detect circular reference objects (coins) outside plant area"""
        try:
            # Work outside plant mask
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (9, 9), 2)
            
            # Detect circles
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=50,
                param1=50,
                param2=30,
                minRadius=15,
                maxRadius=150
            )
            
            if circles is None:
                return {'detected': False, 'type': None}
            
            circles = np.uint16(np.around(circles))
            valid_circles = []
            
            for circle in circles[0]:
                x, y, r = circle
                # Check if circle is outside plant mask
                circle_mask = np.zeros(plant_mask.shape, dtype=np.uint8)
                cv2.circle(circle_mask, (x, y), r, 255, -1)
                overlap = np.sum((circle_mask > 0) & plant_mask) / (np.pi * r * r)
                
                if overlap < 0.2:  # Less than 20% overlap
                    valid_circles.append({
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'diameter_pixels': int(r * 2)
                    })
            
            if not valid_circles:
                return {'detected': False, 'type': None}
            
            # Get largest circle (most likely the reference)
            best = max(valid_circles, key=lambda c: c['radius'])
            
            # Estimate which coin based on diameter ratio
            diameter_px = best['diameter_pixels']
            likely_type = self._estimate_coin_type(diameter_px, image.shape)
            
            return {
                'detected': True,
                'type': 'circle',
                'likely_reference': likely_type,
                'center': best['center'],
                'radius': best['radius'],
                'diameter_pixels': diameter_px,
                'real_size_mm': self.REFERENCE_OBJECTS.get(likely_type, 24.26)
            }
            
        except Exception as e:
            return {'detected': False, 'error': str(e)}
    
    def _estimate_coin_type(self, diameter_px: int, image_shape: tuple) -> str:
        """Estimate coin type based on relative size"""
        # Rough estimation - quarter is most common
        return 'us_quarter'
    
    def detect_rectangular_reference(self, image: np.ndarray,
                                      plant_mask: np.ndarray) -> Dict[str, Any]:
        """Detect rectangular reference objects (cards, rulers)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            rectangles = []
            for cnt in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    if area > 1000:  # Minimum size
                        # Check if outside plant
                        rect_mask = np.zeros(plant_mask.shape, dtype=np.uint8)
                        cv2.drawContours(rect_mask, [approx], -1, 255, -1)
                        overlap = np.sum((rect_mask > 0) & plant_mask) / area
                        
                        if overlap < 0.2:
                            rect = cv2.minAreaRect(cnt)
                            rectangles.append({
                                'contour': approx,
                                'rect': rect,
                                'area': area,
                                'width': max(rect[1]),
                                'height': min(rect[1])
                            })
            
            if not rectangles:
                return {'detected': False, 'type': None}
            
            best = max(rectangles, key=lambda r: r['area'])
            
            # Check aspect ratio for credit card
            ratio = best['width'] / best['height'] if best['height'] > 0 else 0
            if 1.5 < ratio < 1.7:
                likely_type = 'credit_card_width'
            else:
                likely_type = 'unknown_rectangle'
            
            return {
                'detected': True,
                'type': 'rectangle',
                'likely_reference': likely_type,
                'width_pixels': best['width'],
                'height_pixels': best['height'],
                'real_size_mm': self.REFERENCE_OBJECTS.get(likely_type, best['width'] * 0.1)
            }
            
        except Exception as e:
            return {'detected': False, 'error': str(e)}
    
    def calibrate(self, reference_info: Dict[str, Any]) -> Optional[ScaleCalibration]:
        """Calculate scale calibration from detected reference"""
        if not reference_info.get('detected'):
            return None
        
        if reference_info['type'] == 'circle':
            pixels = reference_info['diameter_pixels']
        else:
            pixels = reference_info['width_pixels']
        
        real_mm = reference_info['real_size_mm']
        pixels_per_mm = pixels / real_mm
        
        self.last_calibration = ScaleCalibration(
            pixels_per_mm=pixels_per_mm,
            reference_type=reference_info.get('likely_reference', 'unknown'),
            reference_pixels=pixels,
            real_size_mm=real_mm,
            confidence=0.85 if reference_info['type'] == 'circle' else 0.7
        )
        
        return self.last_calibration
    
    def convert_to_mm(self, pixels: float) -> Optional[float]:
        """Convert pixel measurement to millimeters"""
        if self.last_calibration:
            return pixels / self.last_calibration.pixels_per_mm
        return None
    
    def convert_to_cm(self, pixels: float) -> Optional[float]:
        """Convert pixel measurement to centimeters"""
        mm = self.convert_to_mm(pixels)
        return mm / 10 if mm else None


class PlantMeasurementExtractor:
    """
    Extract comprehensive measurements from plant mask using OpenCV.
    All measurements in pixels, convertible to real units with calibration.
    """
    
    def __init__(self, scale_detector: Optional[ReferenceScaleDetector] = None):
        self.scale = scale_detector or ReferenceScaleDetector()
    
    def extract_all_measurements(self, image: np.ndarray, mask: np.ndarray,
                                  calibration: Optional[ScaleCalibration] = None,
                                  plant_type: str = 'general') -> Dict[str, Any]:
        """
        Extract all available measurements from plant mask.
        
        Args:
            image: Original BGR image
            mask: Binary plant mask from SAM
            calibration: Optional scale calibration
            plant_type: Plant category for specific metrics
            
        Returns:
            Comprehensive measurement dictionary
        """
        measurements = {
            'core_geometry': self._extract_core_geometry(mask),
            'leaf_features': self._extract_leaf_features(image, mask),
            'color_health': self._extract_color_health(image, mask),
            'structural_complexity': self._extract_structural_complexity(mask),
            'spatial_metrics': self._extract_spatial_metrics(mask, image.shape),
            'advanced_features': self._extract_advanced_features(mask),
        }
        
        # Add plant-type specific metrics
        measurements['plant_specific'] = self._extract_plant_specific(
            image, mask, plant_type
        )
        
        # Convert to real units if calibration available
        if calibration:
            measurements['real_units'] = self._convert_to_real_units(
                measurements, calibration
            )
            measurements['calibration'] = {
                'available': True,
                'pixels_per_mm': calibration.pixels_per_mm,
                'reference_type': calibration.reference_type,
                'confidence': calibration.confidence
            }
        else:
            measurements['calibration'] = {'available': False}
        
        return measurements
    
    def _extract_core_geometry(self, mask: np.ndarray) -> Dict[str, Any]:
        """Extract core geometry features"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'error': 'No contours found'}
        
        # Get largest contour
        main_contour = max(contours, key=cv2.contourArea)
        
        # Canopy area (pixel count)
        canopy_area_px = int(np.sum(mask))
        
        # Bounding box
        x, y, w, h = cv2.boundingRect(main_contour)
        
        # Contour measurements
        perimeter = cv2.arcLength(main_contour, True)
        contour_area = cv2.contourArea(main_contour)
        
        # Convex hull
        hull = cv2.convexHull(main_contour)
        hull_area = cv2.contourArea(hull)
        
        # Min enclosing circle
        (cx, cy), radius = cv2.minEnclosingCircle(main_contour)
        
        # Fitted ellipse (if enough points)
        if len(main_contour) >= 5:
            ellipse = cv2.fitEllipse(main_contour)
            ellipse_center = ellipse[0]
            ellipse_axes = ellipse[1]
            ellipse_angle = ellipse[2]
        else:
            ellipse_center = (cx, cy)
            ellipse_axes = (w/2, h/2)
            ellipse_angle = 0
        
        return {
            'canopy_area_px': canopy_area_px,
            'height_px': h,
            'width_px': w,
            'perimeter_px': round(perimeter, 2),
            'bounding_box': {'x': x, 'y': y, 'width': w, 'height': h},
            'bounding_box_area_px': w * h,
            'contour_area_px': int(contour_area),
            'convex_hull_area_px': int(hull_area),
            'enclosing_circle': {
                'center': (int(cx), int(cy)),
                'radius': int(radius),
                'diameter_px': int(radius * 2)
            },
            'fitted_ellipse': {
                'center': (int(ellipse_center[0]), int(ellipse_center[1])),
                'major_axis_px': int(max(ellipse_axes)),
                'minor_axis_px': int(min(ellipse_axes)),
                'angle': round(ellipse_angle, 2)
            },
            'aspect_ratio': round(w / h, 3) if h > 0 else 0,
            'extent': round(contour_area / (w * h), 3) if w * h > 0 else 0,
            'solidity': round(contour_area / hull_area, 3) if hull_area > 0 else 0
        }
    
    def _extract_leaf_features(self, image: np.ndarray, mask: np.ndarray) -> Dict[str, Any]:
        """Extract leaf-related features"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        
        # Edge detection within plant region
        plant_region = cv2.bitwise_and(image, image, mask=mask_uint8)
        gray = cv2.cvtColor(plant_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        edges = cv2.bitwise_and(edges, edges, mask=mask_uint8)
        
        # Find internal contours (potential leaves)
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter by size
        min_leaf_area = np.sum(mask) * 0.005  # 0.5% of plant area
        max_leaf_area = np.sum(mask) * 0.3    # 30% of plant area
        
        leaf_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_leaf_area < area < max_leaf_area:
                leaf_contours.append(cnt)
        
        # Estimate leaf count
        estimated_leaves = len(leaf_contours)
        if estimated_leaves < 3:
            # Use blob detection as fallback
            estimated_leaves = self._estimate_leaves_blob(gray, mask_uint8)
        
        # Leaf density
        contours_main, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_main:
            main_contour = max(contours_main, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(main_contour)
            bbox_area = w * h
            leaf_density = np.sum(mask) / bbox_area if bbox_area > 0 else 0
        else:
            leaf_density = 0
        
        # Foliage coverage (relative to image)
        foliage_coverage = np.sum(mask) / (mask.shape[0] * mask.shape[1])
        
        # Calculate average leaf metrics if we have leaf contours
        avg_leaf_area = 0
        avg_aspect_ratio = 0
        if leaf_contours:
            areas = [cv2.contourArea(c) for c in leaf_contours]
            avg_leaf_area = np.mean(areas)
            
            ratios = []
            for cnt in leaf_contours:
                if len(cnt) >= 5:
                    _, (w, h), _ = cv2.fitEllipse(cnt)
                    if h > 0:
                        ratios.append(max(w, h) / min(w, h))
            avg_aspect_ratio = np.mean(ratios) if ratios else 1.0
        
        return {
            'estimated_leaf_count': max(3, estimated_leaves),
            'leaf_density': round(leaf_density, 4),
            'foliage_coverage_percent': round(foliage_coverage * 100, 2),
            'density_category': 'dense' if leaf_density > 0.7 else 'moderate' if leaf_density > 0.4 else 'sparse',
            'avg_leaf_area_px': int(avg_leaf_area),
            'avg_leaf_aspect_ratio': round(avg_aspect_ratio, 2),
            'leaf_contours_detected': len(leaf_contours)
        }
    
    def _estimate_leaves_blob(self, gray: np.ndarray, mask: np.ndarray) -> int:
        """Estimate leaf count using blob detection"""
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Distance transform
        dist = cv2.distanceTransform(opened, cv2.DIST_L2, 5)
        
        # Find local maxima
        _, thresh = cv2.threshold(dist, 0.3 * dist.max(), 255, cv2.THRESH_BINARY)
        
        # Count connected components
        num_labels, _ = cv2.connectedComponents(thresh.astype(np.uint8))
        
        return max(3, num_labels - 1)  # -1 for background
    
    def _extract_color_health(self, image: np.ndarray, mask: np.ndarray) -> Dict[str, Any]:
        """Extract color and health metrics"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        
        # Convert to different color spaces
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Extract masked regions
        plant_pixels = image[mask]
        plant_hsv = hsv[mask]
        plant_lab = lab[mask]
        
        # Dominant color (mean RGB)
        mean_bgr = np.mean(plant_pixels, axis=0)
        mean_rgb = mean_bgr[::-1]
        
        # HSV analysis
        mean_hsv = np.mean(plant_hsv, axis=0)
        std_hsv = np.std(plant_hsv, axis=0)
        
        # Color ranges for health detection
        total_pixels = np.sum(mask)
        
        # Healthy green detection (HSV: H=35-85, S>40, V>40)
        green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        green_in_plant = cv2.bitwise_and(green_mask, green_mask, mask=mask_uint8)
        green_percent = (np.sum(green_in_plant > 0) / total_pixels) * 100
        
        # Dark green (very healthy)
        dark_green_mask = cv2.inRange(hsv, np.array([35, 80, 40]), np.array([70, 255, 200]))
        dark_green_in_plant = cv2.bitwise_and(dark_green_mask, dark_green_mask, mask=mask_uint8)
        dark_green_percent = (np.sum(dark_green_in_plant > 0) / total_pixels) * 100
        
        # Yellowing detection (HSV: H=15-35)
        yellow_mask = cv2.inRange(hsv, np.array([15, 50, 50]), np.array([35, 255, 255]))
        yellow_in_plant = cv2.bitwise_and(yellow_mask, yellow_mask, mask=mask_uint8)
        yellow_percent = (np.sum(yellow_in_plant > 0) / total_pixels) * 100
        
        # Browning detection (HSV: H=5-20, low S)
        brown_mask = cv2.inRange(hsv, np.array([5, 30, 30]), np.array([20, 200, 200]))
        brown_in_plant = cv2.bitwise_and(brown_mask, brown_mask, mask=mask_uint8)
        brown_percent = (np.sum(brown_in_plant > 0) / total_pixels) * 100
        
        # Vibrancy (saturation)
        vibrancy = np.mean(plant_hsv[:, 1]) / 255 * 100
        
        # Color variance (health indicator)
        color_variance = np.mean(std_hsv)
        
        # LAB analysis for chlorophyll estimation
        # A channel: negative = green, positive = magenta
        # B channel: negative = blue, positive = yellow
        mean_a = np.mean(plant_lab[:, 1]) - 128  # Center at 0
        mean_b = np.mean(plant_lab[:, 2]) - 128
        
        # Chlorophyll proxy (more negative A = more green)
        chlorophyll_index = max(0, min(100, 50 - mean_a))
        
        # Calculate overall health score
        health_score = self._calculate_health_score(
            green_percent, yellow_percent, brown_percent, vibrancy
        )
        
        return {
            'dominant_color_rgb': [int(c) for c in mean_rgb],
            'dominant_color_hsv': [round(c, 1) for c in mean_hsv],
            'green_percentage': round(green_percent, 2),
            'dark_green_percentage': round(dark_green_percent, 2),
            'yellowing_index': round(yellow_percent, 2),
            'browning_index': round(brown_percent, 2),
            'vibrancy': round(vibrancy, 2),
            'color_variance': round(color_variance, 2),
            'chlorophyll_index': round(chlorophyll_index, 2),
            'health_score': round(health_score, 1),
            'health_status': self._get_health_status(health_score),
            'stress_indicators': self._detect_stress(yellow_percent, brown_percent, color_variance)
        }
    
    def _calculate_health_score(self, green: float, yellow: float, 
                                 brown: float, vibrancy: float) -> float:
        """Calculate comprehensive health score (0-100)"""
        # Weighted formula
        score = (
            (green * 0.4) +           # Green coverage
            (vibrancy * 0.25) -        # Color vibrancy
            (yellow * 0.2) -           # Yellowing penalty
            (brown * 0.3)              # Browning penalty
        )
        return max(0, min(100, score))
    
    def _get_health_status(self, score: float) -> str:
        """Convert health score to status"""
        if score >= 80:
            return 'excellent'
        elif score >= 65:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 30:
            return 'poor'
        else:
            return 'critical'
    
    def _detect_stress(self, yellow: float, brown: float, variance: float) -> List[str]:
        """Detect plant stress indicators"""
        indicators = []
        if yellow > 15:
            indicators.append('chlorosis_possible')
        if yellow > 30:
            indicators.append('nutrient_deficiency_likely')
        if brown > 10:
            indicators.append('necrosis_detected')
        if brown > 25:
            indicators.append('disease_or_pest_possible')
        if variance > 50:
            indicators.append('high_color_variance')
        if variance < 10:
            indicators.append('low_color_variance')
        return indicators if indicators else ['no_stress_detected']
    
    def _extract_structural_complexity(self, mask: np.ndarray) -> Dict[str, Any]:
        """Extract structural complexity metrics"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'error': 'No contours'}
        
        main_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(main_contour)
        perimeter = cv2.arcLength(main_contour, True)
        
        # Branching complexity: perimeter² / area
        # Higher value = more complex branching
        branching_complexity = (perimeter ** 2) / area if area > 0 else 0
        
        # Shape compactness: area / convex_hull_area
        hull = cv2.convexHull(main_contour)
        hull_area = cv2.contourArea(hull)
        compactness = area / hull_area if hull_area > 0 else 0
        
        # Convexity defects (indentations)
        hull_indices = cv2.convexHull(main_contour, returnPoints=False)
        if len(hull_indices) > 3:
            defects = cv2.convexityDefects(main_contour, hull_indices)
            num_defects = len(defects) if defects is not None else 0
            
            # Significant defects (deep indentations)
            significant_defects = 0
            if defects is not None:
                for d in defects:
                    depth = d[0][3] / 256.0
                    if depth > 10:  # More than 10 pixels deep
                        significant_defects += 1
        else:
            num_defects = 0
            significant_defects = 0
        
        # Symmetry score (compare left/right halves)
        symmetry = self._calculate_symmetry(mask)
        
        # Circularity
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
        
        return {
            'branching_complexity': round(branching_complexity, 2),
            'shape_compactness': round(compactness, 4),
            'convexity_defects': num_defects,
            'significant_indentations': significant_defects,
            'symmetry_score': round(symmetry, 3),
            'circularity': round(circularity, 4),
            'complexity_category': self._categorize_complexity(branching_complexity)
        }
    
    def _calculate_symmetry(self, mask: np.ndarray) -> float:
        """Calculate left-right symmetry score (0-1)"""
        h, w = mask.shape
        mid = w // 2
        
        left_half = mask[:, :mid]
        right_half = mask[:, mid:mid*2]  # Ensure same size
        right_flipped = np.fliplr(right_half)
        
        # Resize to match if needed
        min_w = min(left_half.shape[1], right_flipped.shape[1])
        left_half = left_half[:, :min_w]
        right_flipped = right_flipped[:, :min_w]
        
        # Calculate overlap
        intersection = np.sum(left_half & right_flipped)
        union = np.sum(left_half | right_flipped)
        
        return intersection / union if union > 0 else 0
    
    def _categorize_complexity(self, complexity: float) -> str:
        """Categorize branching complexity"""
        if complexity < 20:
            return 'simple'
        elif complexity < 50:
            return 'moderate'
        elif complexity < 100:
            return 'complex'
        else:
            return 'highly_complex'
    
    def _extract_spatial_metrics(self, mask: np.ndarray, 
                                  image_shape: tuple) -> Dict[str, Any]:
        """Extract spatial expansion metrics"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'error': 'No contours'}
        
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        
        img_h, img_w = image_shape[:2]
        
        # Ground coverage (relative to image)
        plant_area = np.sum(mask)
        ground_coverage = plant_area / (img_h * img_w)
        
        # Position in frame
        center_x = x + w/2
        center_y = y + h/2
        
        # Radial metrics
        (cx, cy), radius = cv2.minEnclosingCircle(main_contour)
        
        return {
            'height_px': h,
            'width_px': w,
            'aspect_ratio': round(w / h, 3) if h > 0 else 0,
            'ground_coverage_percent': round(ground_coverage * 100, 2),
            'center_position': {'x': int(center_x), 'y': int(center_y)},
            'center_normalized': {
                'x': round(center_x / img_w, 3),
                'y': round(center_y / img_h, 3)
            },
            'enclosing_radius_px': int(radius),
            'enclosing_diameter_px': int(radius * 2),
            'fill_ratio': round(plant_area / (np.pi * radius * radius), 3) if radius > 0 else 0,
            'image_utilization': round((w * h) / (img_w * img_h) * 100, 2)
        }
    
    def _extract_advanced_features(self, mask: np.ndarray) -> Dict[str, Any]:
        """Extract advanced morphological features"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        
        # Skeletonization
        skeleton = morphology.skeletonize(mask)
        skeleton_length = np.sum(skeleton)
        
        # Find branch points in skeleton
        # A branch point has more than 2 neighbors
        branch_points = self._find_branch_points(skeleton)
        
        # End points
        end_points = self._find_end_points(skeleton)
        
        # Fractal dimension approximation (box counting)
        fractal_dim = self._estimate_fractal_dimension(mask)
        
        # Surface roughness (perimeter variation)
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        roughness = 0
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            # Compare actual perimeter to smoothed perimeter
            smooth_perimeter = cv2.arcLength(
                cv2.approxPolyDP(main_contour, 5, True), True
            )
            actual_perimeter = cv2.arcLength(main_contour, True)
            roughness = actual_perimeter / smooth_perimeter if smooth_perimeter > 0 else 1
        
        return {
            'skeleton_length_px': int(skeleton_length),
            'branch_points': int(branch_points),
            'end_points': int(end_points),
            'branching_ratio': round(branch_points / max(1, end_points), 2),
            'fractal_dimension': round(fractal_dim, 3),
            'canopy_roughness': round(roughness, 3),
            'complexity_index': round(skeleton_length / np.sum(mask) * 100, 2) if np.sum(mask) > 0 else 0
        }
    
    def _find_branch_points(self, skeleton: np.ndarray) -> int:
        """Count branch points in skeleton"""
        kernel = np.array([[1, 1, 1],
                          [1, 10, 1],
                          [1, 1, 1]], dtype=np.uint8)
        
        skeleton_uint8 = skeleton.astype(np.uint8)
        neighbors = cv2.filter2D(skeleton_uint8, -1, kernel)
        
        # Branch point: skeleton pixel with >2 neighbors
        # neighbors value > 12 means pixel is skeleton (10) + has >2 neighbors
        branch_points = np.sum((neighbors > 12) & skeleton)
        
        return int(branch_points)
    
    def _find_end_points(self, skeleton: np.ndarray) -> int:
        """Count end points in skeleton"""
        kernel = np.array([[1, 1, 1],
                          [1, 10, 1],
                          [1, 1, 1]], dtype=np.uint8)
        
        skeleton_uint8 = skeleton.astype(np.uint8)
        neighbors = cv2.filter2D(skeleton_uint8, -1, kernel)
        
        # End point: skeleton pixel with exactly 1 neighbor
        # neighbors value = 11 means pixel is skeleton (10) + has 1 neighbor
        end_points = np.sum((neighbors == 11) & skeleton)
        
        return int(end_points)
    
    def _estimate_fractal_dimension(self, mask: np.ndarray) -> float:
        """Estimate fractal dimension using box counting"""
        # Simplified box counting
        sizes = [2, 4, 8, 16, 32, 64]
        counts = []
        
        for size in sizes:
            # Count boxes that contain the object
            h, w = mask.shape
            count = 0
            for i in range(0, h, size):
                for j in range(0, w, size):
                    box = mask[i:min(i+size, h), j:min(j+size, w)]
                    if np.any(box):
                        count += 1
            counts.append(count)
        
        # Linear regression on log-log scale
        if len(counts) > 1 and all(c > 0 for c in counts):
            log_sizes = np.log(sizes[:len(counts)])
            log_counts = np.log(counts)
            
            # Slope of regression line is fractal dimension
            coeffs = np.polyfit(log_sizes, log_counts, 1)
            return -coeffs[0]
        
        return 1.5  # Default
    
    def _extract_plant_specific(self, image: np.ndarray, mask: np.ndarray,
                                 plant_type: str) -> Dict[str, Any]:
        """Extract plant-type specific metrics"""
        mask_uint8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'plant_type': plant_type, 'error': 'No contours'}
        
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        area = np.sum(mask)
        
        metrics = {'plant_type': plant_type}
        
        if plant_type in ['succulent', 'rosette']:
            # Rosette diameter
            metrics['rosette_diameter_px'] = max(w, h)
            metrics['rosette_symmetry'] = self._calculate_symmetry(mask)
            # Leaf thickness proxy (area relative to perimeter)
            perimeter = cv2.arcLength(main_contour, True)
            metrics['leaf_thickness_proxy'] = area / perimeter if perimeter > 0 else 0
            
        elif plant_type in ['vine', 'creeper']:
            # Vine length (skeleton)
            skeleton = morphology.skeletonize(mask)
            metrics['vine_length_px'] = int(np.sum(skeleton))
            metrics['horizontal_spread_px'] = w
            metrics['vertical_extent_px'] = h
            metrics['node_count_estimate'] = self._find_branch_points(skeleton)
            
        elif plant_type in ['bush', 'shrub']:
            metrics['canopy_area_px'] = int(area)
            hull = cv2.convexHull(main_contour)
            hull_area = cv2.contourArea(hull)
            metrics['canopy_density'] = area / hull_area if hull_area > 0 else 0
            skeleton = morphology.skeletonize(mask)
            metrics['branching_complexity'] = self._find_branch_points(skeleton)
            
        elif plant_type == 'tree':
            metrics['height_px'] = h
            metrics['canopy_width_px'] = w
            metrics['canopy_area_px'] = int(area)
            # Trunk estimation (bottom portion)
            bottom_quarter = mask[int(h*0.75):, :]
            metrics['trunk_width_estimate_px'] = np.sum(np.any(bottom_quarter, axis=0))
            
        elif plant_type == 'fern':
            skeleton = morphology.skeletonize(mask)
            metrics['frond_count_estimate'] = self._find_end_points(skeleton)
            metrics['frond_spread_px'] = max(w, h)
            metrics['leaf_cluster_density'] = area / (w * h) if w * h > 0 else 0
            
        elif plant_type == 'tuber':
            # Above-ground metrics
            metrics['leaf_area_px'] = int(area)
            metrics['stem_height_estimate_px'] = h
            # Leaf count from blob detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            metrics['leaf_count_estimate'] = self._estimate_leaves_blob(gray, mask_uint8)
        
        else:  # General
            metrics['area_px'] = int(area)
            metrics['height_px'] = h
            metrics['width_px'] = w
        
        return metrics
    
    def _convert_to_real_units(self, measurements: Dict[str, Any],
                                calibration: ScaleCalibration) -> Dict[str, Any]:
        """Convert pixel measurements to real units (mm, cm)"""
        ppm = calibration.pixels_per_mm
        
        real_units = {}
        
        # Core geometry
        core = measurements.get('core_geometry', {})
        if 'height_px' in core:
            real_units['height_mm'] = round(core['height_px'] / ppm, 2)
            real_units['height_cm'] = round(core['height_px'] / ppm / 10, 2)
        if 'width_px' in core:
            real_units['width_mm'] = round(core['width_px'] / ppm, 2)
            real_units['width_cm'] = round(core['width_px'] / ppm / 10, 2)
        if 'canopy_area_px' in core:
            real_units['canopy_area_mm2'] = round(core['canopy_area_px'] / (ppm ** 2), 2)
            real_units['canopy_area_cm2'] = round(core['canopy_area_px'] / (ppm ** 2) / 100, 2)
        if 'perimeter_px' in core:
            real_units['perimeter_mm'] = round(core['perimeter_px'] / ppm, 2)
            real_units['perimeter_cm'] = round(core['perimeter_px'] / ppm / 10, 2)
        
        # Spatial metrics
        spatial = measurements.get('spatial_metrics', {})
        if 'enclosing_diameter_px' in spatial:
            real_units['enclosing_diameter_mm'] = round(spatial['enclosing_diameter_px'] / ppm, 2)
            real_units['enclosing_diameter_cm'] = round(spatial['enclosing_diameter_px'] / ppm / 10, 2)
        
        # Leaf features
        leaves = measurements.get('leaf_features', {})
        if 'avg_leaf_area_px' in leaves and leaves['avg_leaf_area_px'] > 0:
            real_units['avg_leaf_area_mm2'] = round(leaves['avg_leaf_area_px'] / (ppm ** 2), 2)
        
        # Advanced features
        advanced = measurements.get('advanced_features', {})
        if 'skeleton_length_px' in advanced:
            real_units['skeleton_length_mm'] = round(advanced['skeleton_length_px'] / ppm, 2)
        
        return real_units
    
    def calculate_growth(self, current: Dict[str, Any], 
                         previous: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth metrics between two measurements"""
        growth = {}
        
        # Core geometry growth
        curr_core = current.get('core_geometry', {})
        prev_core = previous.get('core_geometry', {})
        
        if 'canopy_area_px' in curr_core and 'canopy_area_px' in prev_core:
            prev_area = prev_core['canopy_area_px']
            curr_area = curr_core['canopy_area_px']
            if prev_area > 0:
                growth['area_growth_rate'] = round(
                    (curr_area - prev_area) / prev_area * 100, 2
                )
            growth['area_change_px'] = curr_area - prev_area
        
        if 'height_px' in curr_core and 'height_px' in prev_core:
            growth['height_change_px'] = curr_core['height_px'] - prev_core['height_px']
            if prev_core['height_px'] > 0:
                growth['height_growth_rate'] = round(
                    growth['height_change_px'] / prev_core['height_px'] * 100, 2
                )
        
        if 'width_px' in curr_core and 'width_px' in prev_core:
            growth['spread_change_px'] = curr_core['width_px'] - prev_core['width_px']
            if prev_core['width_px'] > 0:
                growth['spread_growth_rate'] = round(
                    growth['spread_change_px'] / prev_core['width_px'] * 100, 2
                )
        
        # Health change
        curr_health = current.get('color_health', {})
        prev_health = previous.get('color_health', {})
        
        if 'health_score' in curr_health and 'health_score' in prev_health:
            growth['health_change'] = round(
                curr_health['health_score'] - prev_health['health_score'], 1
            )
        
        # Growth trend
        if growth:
            area_rate = growth.get('area_growth_rate', 0)
            height_rate = growth.get('height_growth_rate', 0)
            avg_rate = (area_rate + height_rate) / 2
            
            if avg_rate > 5:
                growth['trend'] = 'growing'
            elif avg_rate < -5:
                growth['trend'] = 'declining'
            else:
                growth['trend'] = 'stable'
        
        return growth


class AnnotatedVisualizationGenerator:
    """Generate annotated debug visualizations with all measurements"""
    
    def __init__(self):
        self.colors = {
            'mask': (0, 255, 0),        # Green
            'contour': (0, 255, 255),   # Cyan
            'bbox': (255, 0, 0),        # Blue
            'skeleton': (255, 0, 255),  # Magenta
            'green_health': (0, 200, 0),
            'yellow_health': (0, 165, 255),
            'brown_health': (0, 0, 200),
            'reference': (255, 255, 0),  # Yellow
            'text': (255, 255, 255),     # White
            'text_bg': (0, 0, 0),        # Black
            'branch_point': (0, 0, 255), # Red
            'click_point': (255, 0, 255) # Magenta
        }
    
    def create_comprehensive_visualization(self, 
                                           image: np.ndarray,
                                           mask: np.ndarray,
                                           measurements: Dict[str, Any],
                                           click_point: Optional[Tuple[int, int]] = None,
                                           reference_info: Optional[Dict] = None) -> np.ndarray:
        """
        Create a comprehensive annotated visualization showing all measurements.
        
        Returns: Multi-panel annotated image
        """
        h, w = image.shape[:2]
        
        # Create individual visualization panels
        panel_mask = self._create_mask_panel(image, mask, measurements)
        panel_color = self._create_color_panel(image, mask, measurements)
        panel_structure = self._create_structure_panel(image, mask, measurements)
        panel_metrics = self._create_metrics_panel(w, h, measurements)
        
        # Draw click point on mask panel
        if click_point:
            cv2.circle(panel_mask, click_point, 10, self.colors['click_point'], -1)
            cv2.circle(panel_mask, click_point, 12, (255, 255, 255), 2)
        
        # Draw reference object if detected
        if reference_info and reference_info.get('detected'):
            self._draw_reference(panel_mask, reference_info)
        
        # Combine panels: 2x2 grid
        # [Mask + Geometry] [Color Analysis]
        # [Structure]       [Metrics Text]
        
        top_row = np.hstack([panel_mask, panel_color])
        bottom_row = np.hstack([panel_structure, panel_metrics])
        
        combined = np.vstack([top_row, bottom_row])
        
        return combined
    
    def _create_mask_panel(self, image: np.ndarray, mask: np.ndarray,
                           measurements: Dict[str, Any]) -> np.ndarray:
        """Create panel showing mask, contour, and geometry"""
        panel = image.copy()
        mask_uint8 = (mask.astype(np.uint8)) * 255
        
        # Mask overlay (semi-transparent green)
        mask_overlay = np.zeros_like(image)
        mask_overlay[mask] = self.colors['mask']
        panel = cv2.addWeighted(panel, 0.7, mask_overlay, 0.3, 0)
        
        # Draw contour
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cv2.drawContours(panel, contours, -1, self.colors['contour'], 2)
        
        # Draw bounding box
        core = measurements.get('core_geometry', {})
        bbox = core.get('bounding_box', {})
        if bbox:
            x, y, bw, bh = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            cv2.rectangle(panel, (x, y), (x + bw, y + bh), self.colors['bbox'], 2)
            
            # Annotate dimensions
            self._put_text_with_bg(panel, f"H:{bh}px", (x + bw + 5, y + bh//2))
            self._put_text_with_bg(panel, f"W:{bw}px", (x + bw//2, y - 10))
        
        # Draw enclosing circle
        circle = core.get('enclosing_circle', {})
        if circle:
            center = circle.get('center', (0, 0))
            radius = circle.get('radius', 0)
            cv2.circle(panel, center, radius, (100, 100, 255), 1)
        
        # Draw center point
        spatial = measurements.get('spatial_metrics', {})
        center = spatial.get('center_position', {})
        if center:
            cv2.drawMarker(panel, (center['x'], center['y']), 
                          (255, 255, 0), cv2.MARKER_CROSS, 20, 2)
        
        # Title
        self._put_text_with_bg(panel, "MASK & GEOMETRY", (10, 25), scale=0.7)
        
        return panel
    
    def _create_color_panel(self, image: np.ndarray, mask: np.ndarray,
                            measurements: Dict[str, Any]) -> np.ndarray:
        """Create panel showing color health analysis"""
        panel = image.copy()
        mask_uint8 = (mask.astype(np.uint8)) * 255
        
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create color overlay
        color_overlay = np.zeros_like(image)
        
        # Green regions
        green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        green_in_plant = cv2.bitwise_and(green_mask, green_mask, mask=mask_uint8)
        color_overlay[green_in_plant > 0] = self.colors['green_health']
        
        # Yellow regions
        yellow_mask = cv2.inRange(hsv, np.array([15, 50, 50]), np.array([35, 255, 255]))
        yellow_in_plant = cv2.bitwise_and(yellow_mask, yellow_mask, mask=mask_uint8)
        color_overlay[yellow_in_plant > 0] = self.colors['yellow_health']
        
        # Brown regions
        brown_mask = cv2.inRange(hsv, np.array([5, 30, 30]), np.array([20, 200, 200]))
        brown_in_plant = cv2.bitwise_and(brown_mask, brown_mask, mask=mask_uint8)
        color_overlay[brown_in_plant > 0] = self.colors['brown_health']
        
        # Blend
        panel = cv2.addWeighted(panel, 0.5, color_overlay, 0.5, 0)
        
        # Add health info
        health = measurements.get('color_health', {})
        y_pos = 25
        self._put_text_with_bg(panel, "COLOR ANALYSIS", (10, y_pos), scale=0.7)
        y_pos += 30
        
        score = health.get('health_score', 0)
        status = health.get('health_status', 'unknown')
        color = (0, 255, 0) if score >= 70 else (0, 165, 255) if score >= 50 else (0, 0, 255)
        self._put_text_with_bg(panel, f"Health: {score:.0f}/100 ({status})", 
                               (10, y_pos), color=color)
        
        # Legend
        h, w = panel.shape[:2]
        legend_y = h - 70
        cv2.circle(panel, (20, legend_y), 8, self.colors['green_health'], -1)
        self._put_text_with_bg(panel, "Healthy", (35, legend_y + 5), scale=0.4)
        cv2.circle(panel, (120, legend_y), 8, self.colors['yellow_health'], -1)
        self._put_text_with_bg(panel, "Yellow", (135, legend_y + 5), scale=0.4)
        cv2.circle(panel, (210, legend_y), 8, self.colors['brown_health'], -1)
        self._put_text_with_bg(panel, "Brown", (225, legend_y + 5), scale=0.4)
        
        return panel
    
    def _create_structure_panel(self, image: np.ndarray, mask: np.ndarray,
                                 measurements: Dict[str, Any]) -> np.ndarray:
        """Create panel showing structural features"""
        panel = image.copy()
        
        # Skeletonization
        skeleton = morphology.skeletonize(mask)
        
        # Draw skeleton
        panel[skeleton] = self.colors['skeleton']
        
        # Find and draw branch points
        branch_pts = self._get_branch_point_locations(skeleton)
        for pt in branch_pts[:20]:  # Limit to 20
            cv2.circle(panel, pt, 4, self.colors['branch_point'], -1)
        
        # Draw convex hull
        mask_uint8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(main_contour)
            cv2.drawContours(panel, [hull], -1, (255, 255, 0), 1)
        
        # Title and info
        self._put_text_with_bg(panel, "STRUCTURE ANALYSIS", (10, 25), scale=0.7)
        
        struct = measurements.get('structural_complexity', {})
        adv = measurements.get('advanced_features', {})
        
        y_pos = 50
        self._put_text_with_bg(panel, f"Complexity: {struct.get('complexity_category', 'N/A')}", 
                               (10, y_pos), scale=0.5)
        y_pos += 20
        self._put_text_with_bg(panel, f"Branch pts: {adv.get('branch_points', 0)}", 
                               (10, y_pos), scale=0.5)
        y_pos += 20
        self._put_text_with_bg(panel, f"Symmetry: {struct.get('symmetry_score', 0):.2f}", 
                               (10, y_pos), scale=0.5)
        
        # Legend
        h, w = panel.shape[:2]
        legend_y = h - 50
        cv2.line(panel, (10, legend_y), (30, legend_y), self.colors['skeleton'], 2)
        self._put_text_with_bg(panel, "Skeleton", (35, legend_y + 5), scale=0.4)
        cv2.circle(panel, (120, legend_y), 4, self.colors['branch_point'], -1)
        self._put_text_with_bg(panel, "Branch pt", (130, legend_y + 5), scale=0.4)
        
        return panel
    
    def _create_metrics_panel(self, width: int, height: int,
                               measurements: Dict[str, Any]) -> np.ndarray:
        """Create panel with text metrics summary"""
        panel = np.zeros((height, width, 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)  # Dark gray
        
        y_pos = 25
        line_height = 18
        
        # Title
        cv2.putText(panel, "MEASUREMENTS SUMMARY", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        y_pos += 30
        
        # Core geometry
        core = measurements.get('core_geometry', {})
        cv2.putText(panel, "-- GEOMETRY --", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += line_height
        
        metrics_list = [
            f"Area: {core.get('canopy_area_px', 0):,} px",
            f"Height: {core.get('height_px', 0)} px | Width: {core.get('width_px', 0)} px",
            f"Perimeter: {core.get('perimeter_px', 0):.0f} px",
            f"Aspect: {core.get('aspect_ratio', 0):.2f} | Solidity: {core.get('solidity', 0):.2f}",
        ]
        
        for m in metrics_list:
            cv2.putText(panel, m, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += line_height
        
        y_pos += 5
        
        # Leaf features
        leaves = measurements.get('leaf_features', {})
        cv2.putText(panel, "-- LEAVES --", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += line_height
        
        leaf_metrics = [
            f"Est. count: {leaves.get('estimated_leaf_count', 0)}",
            f"Density: {leaves.get('leaf_density', 0):.3f} ({leaves.get('density_category', 'N/A')})",
            f"Coverage: {leaves.get('foliage_coverage_percent', 0):.1f}%",
        ]
        
        for m in leaf_metrics:
            cv2.putText(panel, m, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += line_height
        
        y_pos += 5
        
        # Color/Health
        health = measurements.get('color_health', {})
        cv2.putText(panel, "-- HEALTH --", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += line_height
        
        health_metrics = [
            f"Score: {health.get('health_score', 0):.0f}/100 ({health.get('health_status', 'N/A')})",
            f"Green: {health.get('green_percentage', 0):.1f}% | Dark green: {health.get('dark_green_percentage', 0):.1f}%",
            f"Yellow: {health.get('yellowing_index', 0):.1f}% | Brown: {health.get('browning_index', 0):.1f}%",
            f"Vibrancy: {health.get('vibrancy', 0):.1f} | Chlorophyll: {health.get('chlorophyll_index', 0):.1f}",
        ]
        
        for m in health_metrics:
            cv2.putText(panel, m, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += line_height
        
        y_pos += 5
        
        # Structural
        struct = measurements.get('structural_complexity', {})
        cv2.putText(panel, "-- STRUCTURE --", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += line_height
        
        struct_metrics = [
            f"Complexity: {struct.get('branching_complexity', 0):.1f} ({struct.get('complexity_category', 'N/A')})",
            f"Compactness: {struct.get('shape_compactness', 0):.3f}",
            f"Symmetry: {struct.get('symmetry_score', 0):.3f}",
            f"Circularity: {struct.get('circularity', 0):.3f}",
        ]
        
        for m in struct_metrics:
            cv2.putText(panel, m, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += line_height
        
        y_pos += 5
        
        # Advanced
        adv = measurements.get('advanced_features', {})
        cv2.putText(panel, "-- ADVANCED --", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += line_height
        
        adv_metrics = [
            f"Skeleton: {adv.get('skeleton_length_px', 0)} px",
            f"Branch pts: {adv.get('branch_points', 0)} | End pts: {adv.get('end_points', 0)}",
            f"Fractal dim: {adv.get('fractal_dimension', 0):.3f}",
            f"Roughness: {adv.get('canopy_roughness', 0):.3f}",
        ]
        
        for m in adv_metrics:
            cv2.putText(panel, m, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += line_height
        
        # Real units if available
        real = measurements.get('real_units', {})
        calib = measurements.get('calibration', {})
        if calib.get('available'):
            y_pos += 10
            cv2.putText(panel, "-- REAL UNITS --", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            y_pos += line_height
            
            real_metrics = [
                f"Height: {real.get('height_cm', 0):.1f} cm | Width: {real.get('width_cm', 0):.1f} cm",
                f"Area: {real.get('canopy_area_cm2', 0):.1f} cm²",
                f"Scale: {calib.get('pixels_per_mm', 0):.2f} px/mm ({calib.get('reference_type', 'N/A')})",
            ]
            
            for m in real_metrics:
                cv2.putText(panel, m, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 100), 1)
                y_pos += line_height
        
        return panel
    
    def _get_branch_point_locations(self, skeleton: np.ndarray) -> List[Tuple[int, int]]:
        """Get coordinates of branch points"""
        kernel = np.array([[1, 1, 1],
                          [1, 10, 1],
                          [1, 1, 1]], dtype=np.uint8)
        
        skeleton_uint8 = skeleton.astype(np.uint8)
        neighbors = cv2.filter2D(skeleton_uint8, -1, kernel)
        
        branch_mask = (neighbors > 12) & skeleton
        points = np.where(branch_mask)
        
        return [(int(x), int(y)) for y, x in zip(points[0], points[1])]
    
    def _draw_reference(self, panel: np.ndarray, ref_info: Dict) -> None:
        """Draw reference object annotation"""
        if ref_info.get('type') == 'circle':
            center = ref_info['center']
            radius = ref_info['radius']
            cv2.circle(panel, center, radius, self.colors['reference'], 2)
            self._put_text_with_bg(panel, f"{ref_info.get('likely_reference', 'ref')}", 
                                   (center[0] - 30, center[1] + radius + 20),
                                   color=self.colors['reference'], scale=0.5)
    
    def _put_text_with_bg(self, img: np.ndarray, text: str, 
                          pos: Tuple[int, int], 
                          color: Tuple[int, int, int] = (255, 255, 255),
                          scale: float = 0.5) -> None:
        """Put text with dark background"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 1
        
        (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
        
        x, y = pos
        cv2.rectangle(img, (x - 2, y - text_h - 2), 
                     (x + text_w + 2, y + baseline + 2),
                     self.colors['text_bg'], -1)
        cv2.putText(img, text, pos, font, scale, color, thickness)
