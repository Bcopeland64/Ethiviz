import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union, Set
import os
import json
from PIL import Image # Use PIL directly
import io
import base64
from dataclasses import dataclass, asdict # Import asdict
from collections import Counter
import logging # Use logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ethiviz.image_analyzer')

# Dependencies (Checks remain the same)
try:
    import cv2
    CV2_AVAILABLE = True
    logger.info("OpenCV (cv2) found.")
except ImportError:
    CV2_AVAILABLE = False
    logger.info("OpenCV (cv2) not found. Using PIL for image operations.")
    from PIL import ImageOps, ImageEnhance # Keep PIL imports here

try:
    import tensorflow as tf
    import tensorflow_hub as hub
    TF_AVAILABLE = True
    logger.info("TensorFlow and TensorFlow Hub found.")
except ImportError:
    TF_AVAILABLE = False
    logger.info("TensorFlow or TensorFlow Hub not found. Deep feature extraction disabled.")


# ImageAnalysisResult Dataclass (Same as previous corrected version)
@dataclass
class ImageAnalysisResult:
    """Container for image analysis results"""
    color_distribution: Dict[str, float]
    skin_tone_distribution: Dict[str, float]
    gender_representation: Dict[str, float]
    age_representation: Dict[str, float]
    cultural_elements: Dict[str, float]
    image_metadata: Dict[str, Any]
    western_ethics_score: float = 0.0
    ubuntu_ethics_score: float = 0.0
    confucian_ethics_score: float = 0.0
    islamic_ethics_score: float = 0.0
    ethics_estimation_confidence: str = "low"
    diversity_index: float = 0.0
    diversity_estimation_confidence: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if "gender_representation" in result: result["gender_distribution"] = result["gender_representation"]
        return result
    def __iter__(self):
        for key, value in self.to_dict().items(): yield key, value
    def keys(self): return self.to_dict().keys()
    def __getitem__(self, key):
        data_dict = self.to_dict()
        if key not in data_dict:
             if key == 'gender_distribution' and 'gender_representation' in data_dict: return data_dict['gender_representation']
             raise KeyError(f"Key '{key}' not found")
        return data_dict[key]


class ImageAnalyzer:
    """
    Analyzes images for bias across multiple ethical dimensions.
    """
    # __init__ and _initialize_feature_extractor remain the same as the previous corrected version
    def __init__(
        self,
        feature_extraction_method: str = "color_histogram",
        use_pretrained_models: bool = False,
        cultural_context: Dict[str, Any] = None,
        batch_size: int = 32
    ):
        self.feature_extraction_method = feature_extraction_method
        self.use_pretrained_models = use_pretrained_models
        self.cultural_context = cultural_context or {}
        self.batch_size = batch_size
        logger.info(f"Initializing ImageAnalyzer with method: {self.feature_extraction_method}, TF: {TF_AVAILABLE}, CV2: {CV2_AVAILABLE}")
        self.skin_tone_references = {
            "type_1_2": np.array([255, 227, 190]), "type_3": np.array([228, 185, 142]),
            "type_4": np.array([198, 134, 66]), "type_5_6": np.array([105, 62, 30])
        }
        self.skin_dist_threshold = 80
        self._initialize_feature_extractor()

    def _initialize_feature_extractor(self):
        self.models = {}; self.hog = None
        chosen_method = self.feature_extraction_method.lower()
        if chosen_method == "deep_features":
            if self.use_pretrained_models and TF_AVAILABLE:
                try:
                    model_url = "https://tfhub.dev/google/tf2-preview/mobilenet_v2/feature_vector/4"
                    self.models["feature_extractor"] = hub.KerasLayer(model_url, trainable=False)
                    self.feature_extraction_method = "deep_features"
                    logger.info(f"Loaded TensorFlow Hub model: {model_url}")
                except Exception as e:
                    logger.error(f"Failed TF Hub load: {e}. Falling back."); fallback = True
                else: fallback = False
                if fallback:
                    if CV2_AVAILABLE: self.feature_extraction_method = "hog"; self.hog = cv2.HOGDescriptor(); logger.info("Falling back to HOG features.")
                    else: self.feature_extraction_method = "color_histogram"; logger.info("Falling back to color histogram.")
            else:
                logger.warning(f"Deep features requested but TF unavailable/disabled. Falling back.")
                if CV2_AVAILABLE: self.feature_extraction_method = "hog"; self.hog = cv2.HOGDescriptor(); logger.info("Falling back to HOG features.")
                else: self.feature_extraction_method = "color_histogram"; logger.info("Falling back to color histogram.")
        elif chosen_method == "hog":
            if CV2_AVAILABLE: self.feature_extraction_method = "hog"; self.hog = cv2.HOGDescriptor(); logger.info("Using HOG features.")
            else: self.feature_extraction_method = "color_histogram"; logger.warning("HOG requested but OpenCV unavailable. Falling back to color histogram.")
        else: self.feature_extraction_method = "color_histogram"; logger.info("Using color histogram features.")


    def analyze_image(self, image_path: str) -> ImageAnalysisResult:
        """ Analyzes a single image. """
        logger.debug(f"Analyzing image: {image_path}")
        try:
            if not os.path.exists(image_path): raise FileNotFoundError(f"Image file not found: {image_path}")
            if CV2_AVAILABLE:
                img = cv2.imread(image_path);
                if img is None: raise ValueError(f"OpenCV could not load image: {image_path}");
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                try: img_pil = Image.open(image_path); img_rgb = np.array(img_pil.convert("RGB"))
                except Exception as pil_e: raise ValueError(f"PIL could not load image: {image_path} ({pil_e})") from pil_e
            if img_rgb.size == 0: raise ValueError(f"Loaded image is empty: {image_path}")

            metadata = self._extract_metadata(image_path, img_rgb)
            color_distribution = self._analyze_color_distribution(img_rgb)
            skin_tone_distribution = self._analyze_skin_tones(img_rgb)
            gender_representation = self._estimate_gender_representation(img_rgb)
            age_representation = self._estimate_age_representation(img_rgb)
            cultural_elements = self._detect_cultural_elements(img_rgb)
            ethics_scores = self._calculate_ethics_scores(cultural_elements)
            diversity_index, diversity_confidence = self._calculate_diversity_index(skin_dist=skin_tone_distribution, gender_dist=gender_representation, age_dist=age_representation)

            return ImageAnalysisResult(
                color_distribution=color_distribution, skin_tone_distribution=skin_tone_distribution,
                gender_representation=gender_representation, age_representation=age_representation,
                cultural_elements=cultural_elements, image_metadata=metadata,
                western_ethics_score=ethics_scores.get("western", 0.0), ubuntu_ethics_score=ethics_scores.get("ubuntu", 0.0),
                confucian_ethics_score=ethics_scores.get("confucian", 0.0), islamic_ethics_score=ethics_scores.get("islamic", 0.0),
                ethics_estimation_confidence=ethics_scores.get("confidence", "low"),
                diversity_index=diversity_index, diversity_estimation_confidence=diversity_confidence )
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}", exc_info=True)
            return ImageAnalysisResult(
                color_distribution={}, skin_tone_distribution={},
                gender_representation={"error": str(e), "estimation_confidence": "error"},
                age_representation={"error": str(e), "estimation_confidence": "error"},
                cultural_elements={"error": str(e), "estimation_confidence": "error"},
                image_metadata={"filename": os.path.basename(image_path), "error": str(e)},
                western_ethics_score=0.0, ubuntu_ethics_score=0.0, confucian_ethics_score=0.0, islamic_ethics_score=0.0,
                ethics_estimation_confidence="error", diversity_index=0.0, diversity_estimation_confidence="error" )


    def _calculate_diversity_index(self, skin_dist: Dict[str, float], gender_dist: Dict[str, float], age_dist: Dict[str, float] ) -> Tuple[float, str]:
        """ Calculates diversity index (0-10). """
        total_diversity_score = 0.0; num_components = 0; confidence_levels = []
        def calculate_shannon_norm(dist_dict):
            valid_items = {k: v for k, v in dist_dict.items() if k not in ["estimation_confidence", "error"] and isinstance(v, (int, float)) and v > 0}
            if not valid_items: return 0.0
            total_value = sum(valid_items.values())
            if total_value <= 0 or len(valid_items) <= 1: return 0.0
            proportions = [v / total_value for v in valid_items.values()]
            shannon_index = -sum(p * np.log(p) for p in proportions)
            max_shannon = np.log(len(valid_items))
            return (shannon_index / max_shannon) if max_shannon > 0 else 0.0

        if skin_dist and "error" not in skin_dist: skin_shannon = calculate_shannon_norm(skin_dist); total_diversity_score += skin_shannon; num_components += 1; confidence_levels.append(1); logger.debug(f"Skin tone Shannon (norm): {skin_shannon:.3f}")
        if gender_dist and "error" not in gender_dist: gender_shannon = calculate_shannon_norm(gender_dist); total_diversity_score += gender_shannon; num_components += 1; confidence_levels.append(0); logger.debug(f"Gender Shannon (norm): {gender_shannon:.3f}")
        if age_dist and "error" not in age_dist: age_shannon = calculate_shannon_norm(age_dist); total_diversity_score += age_shannon; num_components += 1; confidence_levels.append(0); logger.debug(f"Age Shannon (norm): {age_shannon:.3f}")

        if num_components > 0:
             avg_shannon = total_diversity_score / num_components; final_diversity_index = round(avg_shannon * 10.0, 2)
             min_confidence = min(confidence_levels) if confidence_levels else 0; overall_confidence = "very low" if min_confidence == 0 else "low"
        else: final_diversity_index = 0.0; overall_confidence = "N/A (no data)"
        return final_diversity_index, overall_confidence

    def _calculate_ethics_scores(self, cultural_elements: Dict[str, float]) -> Dict[str, Any]:
        """ Estimates ethics scores (proxy). """
        scores = {"western": 0.0, "ubuntu": 0.0, "confucian": 0.0, "islamic": 0.0, "confidence": "low (proxy based on cultural elements)"}
        scale_factor = 10.0; scores["western"] = cultural_elements.get("western", 0.0) * scale_factor
        scores["ubuntu"] = cultural_elements.get("african", 0.0) * scale_factor
        scores["confucian"] = cultural_elements.get("east_asian", 0.0) * scale_factor
        islamic_proxy_score = max(cultural_elements.get("middle_eastern", 0.0), cultural_elements.get("south_asian", 0.0))
        scores["islamic"] = islamic_proxy_score * scale_factor
        for key in ["western", "ubuntu", "confucian", "islamic"]: scores[key] = max(0.0, min(10.0, scores[key]))
        return scores

    def analyze_image_directory(self, directory_path: str) -> Dict[str, ImageAnalysisResult]:
        """ Analyze all images in a directory. """
        logger.info(f"Analyzing images in directory: {directory_path}")
        results = {}; image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        try:
            if not os.path.isdir(directory_path): logger.error(f"Directory not found: {directory_path}"); return {}
            image_files = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path):
                     ext = os.path.splitext(item)[1].lower()
                     if ext in image_extensions: image_files.append(item_path)
            if not image_files: logger.warning(f"No image files found in directory: {directory_path}"); return {}
            logger.info(f"Found {len(image_files)} images to analyze.")
            results = self.batch_process_images(image_files)
        except Exception as e: logger.error(f"Error processing directory {directory_path}: {e}", exc_info=True)
        return results

    def analyze_image_dataset( self, dataset_path: str, image_column: str, metadata_columns: Optional[List[str]] = None, output_path: Optional[str] = None ) -> pd.DataFrame:
        """ Analyze a dataset containing image paths. """
        logger.info(f"Analyzing image dataset: {dataset_path}")
        try:
            if dataset_path.lower().endswith('.csv'): dataset = pd.read_csv(dataset_path)
            elif dataset_path.lower().endswith('.json'):
                 try: dataset = pd.read_json(dataset_path, lines=True if '.jsonl' in dataset_path.lower() else False)
                 except ValueError: dataset = pd.read_json(dataset_path)
            else: raise ValueError("Unsupported dataset format. Use CSV or JSON/JSONL.")
            if image_column not in dataset.columns: raise ValueError(f"Image column '{image_column}' not found in {dataset.columns.tolist()}")
            base_dir = os.path.dirname(dataset_path)
            def resolve_path(p):
                 if isinstance(p, str) and not os.path.isabs(p) and not p.startswith(('http:', 'https:')): resolved = os.path.join(base_dir, p); return resolved if os.path.exists(resolved) else p
                 return p
            dataset[image_column] = dataset[image_column].apply(resolve_path)
            image_paths = dataset[image_column].tolist(); analysis_dict = self.batch_process_images(image_paths)
            results_list = []
            for idx, row in dataset.iterrows():
                image_path = row[image_column]; analysis_result = analysis_dict.get(image_path)
                if analysis_result:
                    result_dict = analysis_result.to_dict()
                    if metadata_columns:
                        for col in metadata_columns:
                            if col in dataset.columns and col != image_column: meta_key = f"meta_{col}" if col in result_dict else col; result_dict["image_metadata"][meta_key] = row[col]
                    result_dict["original_image_path"] = image_path; results_list.append(result_dict)
                else: logger.warning(f"No analysis result for image path: {image_path} (index {idx})")
            results_df = pd.DataFrame(results_list)
            if output_path:
                try: results_df.to_csv(output_path, index=False); logger.info(f"Dataset analysis results saved to: {output_path}")
                except Exception as save_e: logger.error(f"Failed to save dataset results: {save_e}")
            return results_df
        except Exception as e: logger.error(f"Error processing dataset {dataset_path}: {e}", exc_info=True); return pd.DataFrame()


    # --- _extract_metadata MODIFIED ---
    def _extract_metadata(self, image_path: str, img_array: np.ndarray) -> Dict[str, Any]:
        """Extract basic metadata from image"""
        metadata = {}
        try:
            metadata["filename"] = os.path.basename(image_path)
            metadata["width"] = img_array.shape[1]
            metadata["height"] = img_array.shape[0]
            if img_array.shape[0] > 0:
                 metadata["aspect_ratio"] = round(img_array.shape[1] / img_array.shape[0], 3)
            else:
                 metadata["aspect_ratio"] = 0
            metadata["file_size_kb"] = round(os.path.getsize(image_path) / 1024, 2) if os.path.exists(image_path) else 0

            # Try to extract basic EXIF data if PIL is available
            if not CV2_AVAILABLE: # Assume PIL is available if CV2 is not
                try:
                    with Image.open(image_path) as img:
                        exif_data = img.getexif() # Use getexif()
                        if exif_data:
                            exif_subset = {}
                            useful_tags = { 271: "Make", 272: "Model", 305: "Software", 36867: "DateTimeOriginal", 36868: "DateTimeDigitized" }
                            for k, v in exif_data.items():
                                tag_name = useful_tags.get(k)
                                if tag_name:
                                    # --- SYNTAX CORRECTION HERE ---
                                    if isinstance(v, bytes):
                                        try:
                                            # Decode bytes, ignore errors, strip null bytes
                                            v = v.decode('utf-8', errors='ignore').strip('\x00')
                                        except Exception:
                                            # Fallback to string representation if decoding fails
                                            v = str(v)
                                    # --- END CORRECTION ---
                                    # Add to subset, ensuring value is string and stripped
                                    exif_subset[tag_name] = str(v).strip()
                            if exif_subset:
                                 metadata["exif_basic"] = exif_subset
                except UnidentifiedImageError: # Catch specific PIL error
                     logger.warning(f"PIL UnidentifiedImageError for {metadata['filename']}")
                except Exception as exif_e:
                    # Log general exif errors less verbosely unless debugging
                    logger.debug(f"Could not extract EXIF data for {metadata['filename']}: {exif_e}")

        except Exception as meta_e:
             logger.warning(f"Error extracting metadata for {image_path}: {meta_e}")
             metadata["error"] = str(meta_e)

        return metadata
    # --- END _extract_metadata MODIFIED ---


    def _analyze_color_distribution(self, img_array: np.ndarray) -> Dict[str, float]:
        """ Analyze color distribution. """
        # (Same as previous version)
        try:
            bins = 16; hist_combined = []
            if CV2_AVAILABLE:
                for i in range(3): hist = cv2.calcHist([img_array], [i], None, [bins], [0, 256]); cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX); hist_combined.extend(hist.flatten().tolist())
            else:
                 for i in range(3): hist, _ = np.histogram(img_array[:,:,i].ravel(), bins=bins, range=(0, 256), density=True); hist_combined.extend(hist.tolist())
            mean_color = np.mean(img_array, axis=(0, 1)); r, g, b = mean_color
            color_scores = {"red": max(0.0, r - max(g, b)) / 255.0, "green": max(0.0, g - max(r, b)) / 255.0, "blue": max(0.0, b - max(r, g)) / 255.0, "yellow": max(0.0, min(r, g) - b) / 255.0, "cyan": max(0.0, min(g, b) - r) / 255.0, "magenta": max(0.0, min(r, b) - g) / 255.0, "white": min(r, g, b) / 255.0 if min(r, g, b) > 200 else 0.0, "black": (255.0 - max(r, g, b)) / 255.0 if max(r, g, b) < 55 else 0.0, "gray": 1.0 - (abs(r-g)+abs(g-b)+abs(b-r))/510.0 if abs(r-g)<30 and abs(g-b)<30 and 55<=max(r,g,b)<=200 else 0.0}
            total = sum(v for v in color_scores.values() if v > 0)
            if total > 0: normalized_scores = {k: v / total for k, v in color_scores.items() if v > 0}; [normalized_scores.setdefault(k, 0.0) for k in color_scores]; return normalized_scores
            else: return {k: 0.0 for k in color_scores}
        except Exception as e: logger.warning(f"Error analyzing color distribution: {e}"); return {"error": str(e)}

    def _analyze_skin_tones(self, img_array: np.ndarray) -> Dict[str, float]:
        """ Analyze skin tone distribution. """
        # (Same as previous version)
        try:
            skin_tone_counts = {tone: 0 for tone in self.skin_tone_references}; total_skin_pixels = 0; height, width = img_array.shape[:2]
            pixels_to_sample = 10000; step_h = max(1, int(np.sqrt(height * width / pixels_to_sample))); step_w = step_h
            for y in range(0, height, step_h):
                for x in range(0, width, step_w):
                    r, g, b = img_array[y, x]
                    if (r > 95 and g > 40 and b > 20 and r > g and g > b and (r - b) > 15):
                        pixel_rgb = np.array([r, g, b]); min_dist = float('inf'); closest_tone = None
                        for tone, ref_color in self.skin_tone_references.items():
                            dist = np.linalg.norm(pixel_rgb - ref_color)
                            if dist < min_dist: min_dist = dist; closest_tone = tone
                        if min_dist < self.skin_dist_threshold and closest_tone: skin_tone_counts[closest_tone] += 1; total_skin_pixels += 1
            skin_tone_distribution = {};
            if total_skin_pixels > 0: skin_tone_distribution = {tone: round(count / total_skin_pixels, 4) for tone, count in skin_tone_counts.items()}
            else: skin_tone_distribution = {tone: 0.0 for tone in self.skin_tone_references}
            return skin_tone_distribution
        except Exception as e: logger.warning(f"Error analyzing skin tones: {e}"); return {"error": str(e)}

    def _estimate_gender_representation(self, img_array: np.ndarray) -> Dict[str, float]:
        """ Placeholder for gender estimation. """
        # (Same placeholder)
        return {"female": 0.0, "male": 0.0, "unidentified": 1.0, "estimation_confidence": "low (placeholder)"}

    def _estimate_age_representation(self, img_array: np.ndarray) -> Dict[str, float]:
        """ Placeholder for age estimation. """
        # (Same placeholder)
        return {"child": 0.0, "young_adult": 0.0, "adult": 0.0, "senior": 0.0, "unidentified": 1.0, "estimation_confidence": "low (placeholder)"}

    def _detect_cultural_elements(self, img_array: np.ndarray) -> Dict[str, float]:
        """ Placeholder for detecting cultural/geographic elements. """
        # (Same placeholder)
        return {"western": 0.0, "eastern": 0.0, "african": 0.0, "latin_american": 0.0, "indigenous": 0.0, "middle_eastern": 0.0, "south_asian": 0.0, "east_asian": 0.0, "oceanian": 0.0, "unidentified": 1.0, "estimation_confidence": "low (placeholder)"}

    def get_image_embedding(self, img_array: np.ndarray) -> Optional[np.ndarray]:
        """ Extracts feature embedding from image. """
        # (Same as previous version)
        try:
            logger.debug(f"Getting embedding using method: {self.feature_extraction_method}")
            if self.feature_extraction_method == "deep_features" and "feature_extractor" in self.models:
                img_resized = tf.image.resize(img_array, (224, 224)); img_tensor = tf.convert_to_tensor(img_resized); img_tensor = tf.expand_dims(img_tensor, 0); img_tensor = tf.keras.applications.mobilenet_v2.preprocess_input(img_tensor)
                embedding = self.models["feature_extractor"](img_tensor); return embedding.numpy().flatten()
            elif self.feature_extraction_method == "hog" and self.hog:
                if img_array.ndim == 3 and img_array.shape[2] == 3: img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                elif img_array.ndim == 2: img_gray = img_array
                else: logger.warning("Unsupported image format for HOG."); return None
                img_resized = cv2.resize(img_gray, (64, 128)); hog_features = self.hog.compute(img_resized); return hog_features.flatten() if hog_features is not None else None
            else: # Default to color histogram
                hist_features = [];
                for i in range(3): hist, _ = np.histogram(img_array[:,:,i].ravel(), bins=32, range=(0, 256), density=True); hist_features.extend(hist.tolist())
                return np.array(hist_features)
        except Exception as e: logger.error(f"Error getting image embedding: {e}", exc_info=True); return None

    def batch_process_images(self, image_paths: List[str]) -> Dict[str, ImageAnalysisResult]:
        """ Processes multiple images. """
        # (Same as previous version)
        results = {}; num_images = len(image_paths);
        if not num_images: return results;
        logger.info(f"Starting batch processing for {num_images} images...")
        for i in range(0, num_images, self.batch_size):
            batch_paths = image_paths[i:min(i + self.batch_size, num_images)]
            logger.debug(f"Processing batch {i//self.batch_size + 1}/{(num_images + self.batch_size - 1)//self.batch_size} ({len(batch_paths)} images)")
            for path in batch_paths: results[path] = self.analyze_image(path)
        logger.info(f"Finished batch processing {len(results)} images."); return results

    def get_aggregated_analysis(self, analysis_results: List[ImageAnalysisResult]) -> Dict[str, Any]:
        """ Aggregates analysis results. """
        # (Same as previous corrected version with diversity index)
        if not analysis_results: logger.warning("No results for aggregation."); return {}
        agg_data = {"color_distribution": {}, "skin_tone_distribution": {}, "gender_representation": {}, "age_representation": {}, "cultural_elements": {}, "western_ethics_score": [], "ubuntu_ethics_score": [], "confucian_ethics_score": [], "islamic_ethics_score": [], "diversity_index": [], "image_metadata_list": []}
        valid_results_count = 0
        for result in analysis_results:
            if isinstance(result.image_metadata.get("error"), str): continue
            valid_results_count += 1; agg_data["image_metadata_list"].append(result.image_metadata)
            for key in ["color_distribution", "skin_tone_distribution", "gender_representation", "age_representation", "cultural_elements"]:
                field_data = getattr(result, key, {}); items_to_agg = {k: v for k, v in field_data.items() if k not in ["estimation_confidence", "error"]}
                for sub_key, value in items_to_agg.items():
                     numeric_value = pd.to_numeric(value, errors='coerce')
                     if pd.notna(numeric_value): agg_data[key].setdefault(sub_key, []).append(numeric_value)
            for key in ["western_ethics_score", "ubuntu_ethics_score", "confucian_ethics_score", "islamic_ethics_score", "diversity_index"]:
                 score = getattr(result, key, 0.0); agg_data[key].append(score)
        if valid_results_count == 0: logger.warning("No valid results for aggregation."); return {"error": "No valid image results to aggregate."}
        aggregated_results = {}
        for key in ["color_distribution", "skin_tone_distribution", "gender_representation", "age_representation", "cultural_elements"]:
             aggregated_results[key] = { sub_key: round(np.mean(values), 4) for sub_key, values in agg_data[key].items() if values }
             if hasattr(analysis_results[0], key) and "estimation_confidence" in getattr(analysis_results[0], key, {}): aggregated_results[key]["estimation_confidence"] = getattr(analysis_results[0], key)["estimation_confidence"]
        for key in ["western_ethics_score", "ubuntu_ethics_score", "confucian_ethics_score", "islamic_ethics_score", "diversity_index"]:
             aggregated_results[key] = round(np.mean(agg_data[key]), 4) if agg_data[key] else 0.0
        if hasattr(analysis_results[0], 'ethics_estimation_confidence'): aggregated_results["ethics_estimation_confidence"] = analysis_results[0].ethics_estimation_confidence
        if hasattr(analysis_results[0], 'diversity_estimation_confidence'): aggregated_results["diversity_estimation_confidence"] = analysis_results[0].diversity_estimation_confidence
        aggregated_results["sample_size"] = valid_results_count; logger.info(f"Aggregation complete for {valid_results_count} valid images."); return aggregated_results

    def run_image_analysis_and_save( self, image_dir_or_dataset: str, output_dir: str, is_dataset: bool = False, image_column: Optional[str] = None, metadata_columns: Optional[List[str]] = None, feature_extraction_method: str = "color_histogram", use_pretrained_models: bool = False, cultural_context: Optional[Dict[str, Any]] = None, batch_size: int = 32 ):
        """ Runs image analysis and saves results. """
        # (Same as previous version)
        logger.info("Starting image analysis run..."); os.makedirs(output_dir, exist_ok=True)
        try:
            analyzer = ImageAnalyzer(feature_extraction_method=feature_extraction_method, use_pretrained_models=use_pretrained_models, cultural_context=cultural_context, batch_size=batch_size)
            results_list = []; results_df = pd.DataFrame()
            if is_dataset:
                if not image_column: raise ValueError("image_column must be specified when is_dataset=True")
                results_df = analyzer.analyze_image_dataset(dataset_path=image_dir_or_dataset, image_column=image_column, metadata_columns=metadata_columns)
                image_paths_from_df = results_df['original_image_path'].tolist() if 'original_image_path' in results_df else []; results_dict_from_df = analyzer.batch_process_images(image_paths_from_df); results_list = list(results_dict_from_df.values())
            else: # Directory
                results_dict = analyzer.analyze_image_directory(image_dir_or_dataset); results_list = list(results_dict.values())
                results_list_for_df = [];
                for image_path, result_obj in results_dict.items(): row = result_obj.to_dict(); row['image_path'] = image_path; results_list_for_df.append(row)
                if results_list_for_df: results_df = pd.DataFrame(results_list_for_df)
            raw_results_path = None
            if not results_df.empty:
                 raw_results_path = os.path.join(output_dir, "image_analysis_raw_results.csv");
                 try: results_df.to_csv(raw_results_path, index=False); logger.info(f"Raw results saved: {raw_results_path}")
                 except Exception as save_e: logger.error(f"Failed raw save: {save_e}"); raw_results_path = None
            else: logger.warning("No raw results to save.")
            aggregated_results_path = None
            if results_list:
                aggregated_results = analyzer.get_aggregated_analysis(results_list)
                if aggregated_results and 'error' not in aggregated_results:
                    aggregated_results_path = os.path.join(output_dir, "image_analysis_aggregated_results.json");
                    try:
                        with open(aggregated_results_path, 'w', encoding='utf-8') as f: json.dump(aggregated_results, f, indent=2, ensure_ascii=False, default=lambda x: x.item() if isinstance(x, np.generic) else str(x))
                        logger.info(f"Aggregated results saved: {aggregated_results_path}")
                    except Exception as save_e: logger.error(f"Failed aggregated save: {save_e}"); aggregated_results_path = None
                elif aggregated_results: logger.error(f"Aggregation failed: {aggregated_results.get('error')}")
                else: logger.warning("Aggregation yielded no results.")
            else: logger.warning("No individual results for aggregation.")
            logger.info(f"Image analysis process finished for {image_dir_or_dataset}")
            return {"raw_results_path": raw_results_path, "aggregated_results_path": aggregated_results_path, "output_dir": output_dir}
        except Exception as e: logger.error(f"Fatal error during image analysis run: {e}", exc_info=True); return None


# Example usage (remains the same)
if __name__ == "__main__":
    sample_dir = "sample_images"
    if not os.path.isdir(sample_dir): print(f"Creating dummy sample directory: {sample_dir}"); os.makedirs(sample_dir, exist_ok=True);
    if not os.listdir(sample_dir): # Add dummy image only if directory is empty
        try: dummy_img = Image.new('RGB', (60, 30), color = ('#ADD8E6')); dummy_img.save(os.path.join(sample_dir, "dummy_placeholder.png")); print("Created dummy placeholder image.")
        except Exception as e: print(f"Could not create dummy image: {e}")
    print("\nRunning image analysis on directory...")
    # Instantiate analyzer first to call the instance method
    analyzer_instance = ImageAnalyzer()
    analysis_output = analyzer_instance.run_image_analysis_and_save(image_dir_or_dataset=sample_dir, output_dir="image_analysis_output", batch_size=4)
    if analysis_output: print(f"\nAnalysis complete. Results saved to: {analysis_output['output_dir']}")
    else: print("\nImage analysis run failed.")