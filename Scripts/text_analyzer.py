# text_analyzer.py

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union, Set
import os
import json
import re
from dataclasses import dataclass, asdict  # Import asdict as an alternative for dataclasses
from collections import Counter
import logging # Use logging for better feedback control

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Dependency Availability Check ---
try:
    import spacy
    SPACY_AVAILABLE = True
    # Attempt to load model early to check if it's installed
    try:
        spacy.load("en_core_web_sm") # Check default model existence
        SPACY_MODEL_AVAILABLE = True
    except OSError:
        SPACY_MODEL_AVAILABLE = False
        logging.warning("Default spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    SPACY_MODEL_AVAILABLE = False
    logging.info("spaCy library not found. spaCy processing will be disabled.")

try:
    # Check for transformers and tensorflow/pytorch
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    # More robust check for underlying framework
    try:
        import torch
        TRANSFORMERS_BACKEND_AVAILABLE = True
    except ImportError:
        try:
            import tensorflow
            TRANSFORMERS_BACKEND_AVAILABLE = True
        except ImportError:
             TRANSFORMERS_BACKEND_AVAILABLE = False
             logging.warning("Transformers library found, but neither PyTorch nor TensorFlow detected. Transformers pipelines may not work.")

except ImportError:
    TRANSFORMERS_AVAILABLE = False
    TRANSFORMERS_BACKEND_AVAILABLE = False
    logging.info("Transformers library not found. Transformer-based processing will be disabled.")

# --- NLTK Initialization Block (Modified) ---
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    logging.info("NLTK library found. Initializing resources...")

    # Ensure required NLTK data is downloaded
    def download_nltk_resource(resource_id, resource_path):
        try:
            nltk.data.find(resource_path)
            logging.info(f"NLTK resource '{resource_id}' found at default paths.")
            return True # Resource found
        except LookupError:
            logging.warning(f"NLTK resource '{resource_id}' not found. Attempting download...")
            try:
                # Use quiet=False for visibility during download
                nltk.download(resource_id, quiet=False)
                # Verify download by finding again
                nltk.data.find(resource_path)
                logging.info(f"NLTK resource '{resource_id}' downloaded successfully.")
                return True # Resource downloaded
            except Exception as download_error:
                logging.error(f"Error downloading NLTK resource '{resource_id}': {download_error}", exc_info=True)
                logging.error(f"Please try running 'python -m nltk.downloader {resource_id}' manually in your environment.")
                return False # Download failed
        except Exception as find_error:
             logging.error(f"Unexpected error finding NLTK resource '{resource_id}': {find_error}", exc_info=True)
             return False # Unexpected error

    # Track overall NLTK readiness based on essential resources
    nltk_ready = True
    # Download 'punkt' (essential for word_tokenize)
    if not download_nltk_resource('punkt', 'tokenizers/punkt'):
        nltk_ready = False
        logging.error("'punkt' resource is essential for NLTK tokenization.")

    # Download 'stopwords' (used in preprocessing)
    if not download_nltk_resource('stopwords', 'corpora/stopwords'):
        # Might not be critical depending on preprocessing choices, but log it
        logging.warning("'stopwords' resource download failed, preprocessing might be affected.")

    # Download 'punkt_tab' (specific tokenizer variant needed based on original error)
    if not download_nltk_resource('punkt_tab', 'tokenizers/punkt_tab'):
        # This might be optional unless specific text structures trigger it
        logging.warning("'punkt_tab' resource download failed. Tokenization might fail on certain inputs.")

    # If essential NLTK resources failed, mark NLTK as unavailable for core tasks
    if not nltk_ready:
        NLTK_AVAILABLE = False
        logging.error("Essential NLTK resources could not be verified or downloaded. NLTK processing will be limited or disabled.")

except ImportError:
    NLTK_AVAILABLE = False
    logging.info("NLTK library not found. NLTK-based processing will be skipped.")
except Exception as e:
    # Catch potential errors during the NLTK setup/download process
    NLTK_AVAILABLE = False
    logging.error(f"An unexpected error occurred during NLTK setup or data download: {e}", exc_info=True)
# --- End of NLTK Initialization Block ---


@dataclass
class TextAnalysisResult:
    """Container for text analysis results"""
    bias_score: float
    diversity_index: float
    western_ethics_score: float
    ubuntu_ethics_score: float
    confucian_ethics_score: float
    islamic_ethics_score: float
    cultural_markers: Dict[str, float]
    demographic_representation: Dict[str, float]
    text_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return asdict(self)

class TextAnalyzer:
    """
    Analyzes text data for bias across multiple ethical frameworks.
    Uses a tiered approach to balance accuracy with computational efficiency.
    """

    def __init__(
        self,
        traditions: Optional[List[str]] = None,
        nlp_engine: str = 'auto', # 'spacy', 'nltk', 'basic', 'auto'
        spacy_model: str = "en_core_web_sm",
        use_transformers: bool = False,
        max_tokens: int = 10000,
        batch_size: int = 32
    ):
        """
        Initialize the text analyzer with configurable parameters.

        Parameters:
        -----------
        traditions : List[str], optional
            List of ethical traditions to analyze against. Defaults to all.
            Options: "western", "ubuntu", "confucian", "islamic"

        nlp_engine : str, optional
             Preferred NLP engine: 'spacy', 'nltk', 'basic', or 'auto'.
             'auto' prioritizes spaCy > NLTK > basic based on availability. Defaults to 'auto'.

        spacy_model : str, optional
            SpaCy model to use if nlp_engine is 'spacy' or 'auto'. Defaults to "en_core_web_sm".

        use_transformers : bool, optional
            Whether to attempt using transformers for sentiment analysis. Requires transformers and a backend (torch/tf). Defaults to False.

        max_tokens : int, optional
            Maximum number of tokens to process per text after tokenization. Defaults to 10000.

        batch_size : int, optional
            Number of texts to process in a batch for list/DataFrame inputs. Defaults to 32.
        """
        # Store configuration
        self.traditions = traditions or ["western", "ubuntu", "confucian", "islamic"]
        self.spacy_model_name = spacy_model
        self.attempt_transformers = use_transformers
        self.max_tokens = max_tokens
        self.batch_size = batch_size

        # Determine and initialize NLP engine
        self.nlp_engine_pref = nlp_engine.lower()
        self._initialize_nlp_tools()

        # Load ethical frameworks
        self._load_ethical_frameworks()

        logging.info(f"TextAnalyzer initialized. NLP Engine: {self.active_nlp_engine}, Transformers Sentiment: {self.sentiment_analyzer is not None}")


    def _initialize_nlp_tools(self):
        """Initialize NLP tools based on availability and preference"""
        self.nlp = None # For spaCy model object
        self.sentiment_analyzer = None
        self.active_nlp_engine = 'none' # Track which engine is active

        # Determine NLP engine based on preference and availability
        if self.nlp_engine_pref == 'spacy' or self.nlp_engine_pref == 'auto':
            if SPACY_AVAILABLE and SPACY_MODEL_AVAILABLE:
                try:
                    self.nlp = spacy.load(self.spacy_model_name)
                    self.active_nlp_engine = 'spacy'
                    logging.info(f"Using spaCy NLP engine with model: {self.spacy_model_name}")
                except Exception as e:
                    logging.error(f"Failed to load spaCy model '{self.spacy_model_name}': {e}. Falling back.", exc_info=True)
                    if self.nlp_engine_pref == 'spacy': # If spaCy was explicitly requested, stop here or fall back harder
                         logging.error("spaCy was explicitly requested but failed to load. NLP features will be limited.")
                         self.active_nlp_engine = 'basic' # Fallback to basic if spacy load fails

            elif self.nlp_engine_pref == 'spacy':
                 logging.warning("spaCy requested but not available or model missing. Falling back to NLTK/basic.")
                 # Fall through to check NLTK if auto, or stick with basic if spacy was forced

        if self.active_nlp_engine == 'none' and (self.nlp_engine_pref == 'nltk' or self.nlp_engine_pref == 'auto'):
             if NLTK_AVAILABLE and nltk_ready: # Check if NLTK lib and essential resources are ready
                  self.active_nlp_engine = 'nltk'
                  logging.info("Using NLTK NLP engine.")
             elif self.nlp_engine_pref == 'nltk':
                  logging.warning("NLTK requested but not available or resources missing. Falling back to basic.")
                  self.active_nlp_engine = 'basic'

        # If still no engine after checking preferences, default to basic
        if self.active_nlp_engine == 'none':
             self.active_nlp_engine = 'basic'
             logging.info("Using basic string processing for NLP tasks.")


        # Initialize transformers if available, requested, and backend exists
        if self.attempt_transformers and TRANSFORMERS_AVAILABLE and TRANSFORMERS_BACKEND_AVAILABLE:
            try:
                # Using a specific, potentially smaller model for sentiment might be better
                self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
                logging.info("Loaded transformers sentiment analysis pipeline (distilbert-sst-2).")
            except Exception as e:
                logging.error(f"Failed to load default transformers sentiment pipeline: {e}. Trying generic pipeline...", exc_info=True)
                try:
                     # Fallback to generic pipeline which might download a default model
                     self.sentiment_analyzer = pipeline("sentiment-analysis")
                     logging.info("Loaded generic transformers sentiment analysis pipeline.")
                except Exception as e2:
                     logging.error(f"Failed to load generic transformers pipeline: {e2}. Sentiment analysis disabled.", exc_info=True)
                     self.sentiment_analyzer = None # Ensure it's None if loading failed
        elif self.attempt_transformers:
            if not TRANSFORMERS_AVAILABLE:
                 logging.warning("Transformers requested but library not found. Skipping transformer-based analysis.")
            elif not TRANSFORMERS_BACKEND_AVAILABLE:
                 logging.warning("Transformers found, but no backend (PyTorch/TensorFlow) detected. Skipping transformer-based analysis.")


    def _load_ethical_frameworks(self):
        """Load ethical frameworks and their key terms"""
        # Keywords associated with each ethical tradition
        # (Using the same definitions as before)
        self.ethical_frameworks = {
            "western": {
                "keywords": [
                    "autonomy", "freedom", "rights", "individual", "liberty", "consent",
                    "equality", "fairness", "justice", "democracy", "choice", "privacy",
                    "transparency", "accountability", "rationality", "objectivity"
                ],
                "bias_markers": [
                    "universal", "objective", "rational", "modern", "developed",
                    "advanced", "civilized", "progressive", "superior"
                ]
            },
            "ubuntu": {
                "keywords": [
                    "community", "harmony", "interdependence", "consensus", "solidarity",
                    "sharing", "reciprocity", "belonging", "generosity", "compassion",
                    "dignity", "humanity", "respect", "relationship", "kinship", "collective"
                ],
                "bias_markers": [
                    "traditional", "tribal", "undeveloped", "simple", "primitive",
                    "exotic", "native", "indigenous", "spiritual"
                ]
            },
            "confucian": {
                "keywords": [
                    "harmony", "respect", "filial", "hierarchy", "duty", "loyalty",
                    "ritual", "tradition", "wisdom", "benevolence", "cultivation",
                    "virtue", "propriety", "ancestors", "family", "honor", "moderation"
                ],
                "bias_markers": [
                    "obedient", "collectivist", "authoritarian", "hierarchical",
                    "ancient", "mysterious", "exotic", "rigid", "structured"
                ]
            },
            "islamic": {
                "keywords": [
                    "justice", "charity", "compassion", "mercy", "community", "balance",
                    "equity", "responsibility", "stewardship", "harmony", "moderation",
                    "intention", "peace", "dignity", "respect", "kindness", "brotherhood"
                ],
                "bias_markers": [
                    "fundamentalist", "strict", "rigid", "traditional", "dogmatic",
                    "oppressive", "backward", "theocratic", "exotic", "fanatical"
                ]
            }
        }

        # Cultural markers for detecting representation of different cultures
        # (Using the same definitions as before)
        self.cultural_markers = {
            "western": [
                "europe", "america", "western", "european", "american", "christianity",
                "democracy", "capitalism", "individualism", "enlightenment", "renaissance"
            ],
            "african": [
                "africa", "african", "ubuntu", "tribe", "community", "oral", "traditional",
                "indigenous", "native", "collective", "ancestral"
            ],
            "east_asian": [
                "china", "japan", "korea", "chinese", "japanese", "korean", "confucian",
                "taoist", "buddhist", "harmony", "filial", "collective", "honor"
            ],
            "islamic": [
                "islam", "muslim", "islamic", "quran", "mosque", "halal", "ramadan",
                "community", "ummah", "shariah", "middle east", "arabic"
            ],
            "south_asian": [
                "india", "pakistan", "bangladesh", "hindu", "dharma", "karma", "yoga",
                "sanskrit", "caste", "family", "tradition", "spirituality"
            ],
            "indigenous": [
                "native", "tribal", "indigenous", "aboriginal", "first nations", "community",
                "land", "spiritual", "traditional", "elder", "ceremony", "connection"
            ]
        }

        # Demographic markers for detecting representation of different groups
        # (Using the same definitions as before)
        self.demographic_markers = {
            "gender": {
                "male": ["man", "men", "male", "boy", "boys", "he", "him", "his", "husband", "father"],
                "female": ["woman", "women", "female", "girl", "girls", "she", "her", "hers", "wife", "mother"],
                "nonbinary": ["nonbinary", "non-binary", "genderqueer", "gender-fluid", "they", "them", "their", "themself"]
            },
            "age": {
                "child": ["child", "children", "kid", "kids", "young", "youth", "teenager", "teen", "adolescent"],
                "adult": ["adult", "grown", "mature", "middle-aged", "professional", "worker"],
                "senior": ["senior", "elderly", "aging", "retired", "elder", "old"]
            }
        }
        logging.info("Ethical frameworks, cultural, and demographic markers loaded.")

    def analyze(self, text_data) -> Union[TextAnalysisResult, List[TextAnalysisResult], None]:
        """
        Analyze text data for bias across multiple ethical frameworks.

        Parameters:
        -----------
        text_data : str, list, pd.Series, or pd.DataFrame
            Text data to analyze. Can be a single string, list/Series of strings,
            or a DataFrame with a 'text' column.

        Returns:
        --------
        Union[TextAnalysisResult, List[TextAnalysisResult], None]
            Analysis result(s) or None if input is invalid.
        """
        try:
            if isinstance(text_data, str):
                # Check if it's a file path that exists
                if os.path.isfile(text_data):
                    logging.info(f"Input is a file path: {text_data}. Reading file...")
                    return self._analyze_file(text_data)
                else:
                    # Assume it's a text string
                    logging.info("Analyzing single text string.")
                    return self._analyze_text(text_data)
            elif isinstance(text_data, list):
                logging.info(f"Analyzing list of {len(text_data)} texts using batch processing.")
                if not all(isinstance(item, str) for item in text_data):
                    logging.warning("Input list contains non-string elements. Attempting conversion to string.")
                    text_list = [str(item) for item in text_data]
                else:
                    text_list = text_data
                return self.batch_analyze(text_list)
            elif isinstance(text_data, pd.Series):
                logging.info(f"Analyzing pandas Series of {len(text_data)} texts using batch processing.")
                return self.batch_analyze(text_data.astype(str).tolist())
            elif isinstance(text_data, pd.DataFrame):
                if 'text' in text_data.columns:
                    logging.info(f"Analyzing 'text' column from DataFrame with {len(text_data)} rows using batch processing.")
                    return self.batch_analyze(text_data['text'].astype(str).tolist())
                else:
                    logging.error("Input DataFrame does not have a 'text' column.")
                    raise ValueError("DataFrame must have a 'text' column")
            else:
                logging.error(f"Unsupported input type: {type(text_data)}. Please provide a string, list, pd.Series, or pd.DataFrame.")
                raise ValueError(f"Unsupported input type: {type(text_data)}")
        except Exception as e:
             logging.error(f"Error during analysis dispatcher: {e}", exc_info=True)
             return None # Return None or raise the exception depending on desired behavior

    def _analyze_file(self, file_path: str) -> Union[TextAnalysisResult, List[TextAnalysisResult]]:
        """Analyze text from a file"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            logging.info(f"Processing file {file_path} with extension {file_extension}")

            if file_extension == '.csv':
                # Handle potential CSV reading issues
                try:
                     df = pd.read_csv(file_path)
                except pd.errors.ParserError as pe:
                     logging.error(f"CSV parsing error in {file_path}: {pe}. Check CSV format/delimiters.")
                     raise ValueError(f"Invalid CSV format in {file_path}") from pe
                except Exception as read_err:
                     logging.error(f"Error reading CSV {file_path}: {read_err}")
                     raise IOError(f"Could not read CSV file {file_path}") from read_err

                if 'text' in df.columns:
                    return self.batch_analyze(df['text'].astype(str).tolist())
                else:
                    raise ValueError("CSV file must have a 'text' column")

            elif file_extension == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as jde:
                        logging.error(f"Invalid JSON format in {file_path}: {jde}")
                        raise ValueError(f"Invalid JSON format in {file_path}") from jde

                if isinstance(data, list):
                    if not data: return [] # Handle empty list
                    # Check if list of strings or list of dicts with 'text' key
                    if all(isinstance(item, str) for item in data):
                        return self.batch_analyze(data)
                    elif all(isinstance(item, dict) and 'text' in item for item in data):
                        return self.batch_analyze([str(item['text']) for item in data])
                    else:
                        raise ValueError("JSON list items must be strings OR objects with a 'text' field")
                elif isinstance(data, dict) and 'text' in data:
                    return self._analyze_text(str(data['text']))
                else:
                    raise ValueError("JSON file must contain a list (of strings or objects with 'text') OR a single object with a 'text' field")

            elif file_extension in ('.txt', '.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                return self._analyze_text(text)

            else:
                raise ValueError(f"Unsupported file type: {file_extension}. Supported types: .csv, .json, .txt, .md")

        except FileNotFoundError:
            logging.error(f"File not found at path: {file_path}")
            raise FileNotFoundError(f"Error: File not found at {file_path}")
        except ValueError as ve: # Catch specific format errors
             logging.error(f"Format error processing file {file_path}: {ve}")
             raise # Re-raise value errors (like missing columns, bad JSON)
        except Exception as e:
             # Catch other potential errors (IOError, permissions, etc.)
             logging.error(f"An unexpected error occurred processing file {file_path}: {e}", exc_info=True)
             raise RuntimeError(f"Error processing file {file_path}") from e


    def _analyze_text(self, text: str) -> TextAnalysisResult:
        """Analyze a single text document"""
        # Ensure text is a string
        if not isinstance(text, str):
           logging.warning(f"Input text is not a string ({type(text)}), attempting conversion.")
           text = str(text)

        if not text.strip():
             logging.warning("Input text is empty or whitespace only. Returning default results.")
             # Return a result with default/zero values for empty input
             return TextAnalysisResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, {}, {"length_chars": 0, "word_count": 0, "sentence_count": 0, "unique_words_approx": 0, "sentiment": "N/A", "sentiment_score": 0.0})

        logging.debug(f"Analyzing text snippet: '{text[:100]}...'")

        # Preprocess text using the determined engine
        tokens = self._preprocess_text(text)

        # Calculate metrics
        bias_score = self._calculate_bias_score(text, tokens)
        diversity_index = self._calculate_diversity_index(text, tokens)
        ethics_scores = {f"{tradition}_ethics_score": self._calculate_ethics_score(tradition, text, tokens)
                         for tradition in self.traditions}
        cultural_markers = self._identify_cultural_markers(text, tokens)
        demographic_representation = self._analyze_demographics(text, tokens)
        metadata = self._extract_metadata(text, tokens)

        # Create result object (round final scores for readability)
        result = TextAnalysisResult(
            bias_score=round(bias_score, 2),
            diversity_index=round(diversity_index, 2),
            western_ethics_score=round(ethics_scores.get("western_ethics_score", 0.0), 2),
            ubuntu_ethics_score=round(ethics_scores.get("ubuntu_ethics_score", 0.0), 2),
            confucian_ethics_score=round(ethics_scores.get("confucian_ethics_score", 0.0), 2),
            islamic_ethics_score=round(ethics_scores.get("islamic_ethics_score", 0.0), 2),
            cultural_markers={k: round(v, 4) for k, v in cultural_markers.items()},
            demographic_representation={k: round(v, 4) for k, v in demographic_representation.items()},
            text_metadata=metadata
        )
        logging.debug(f"Analysis complete for text snippet. Bias Score: {result.bias_score}, Diversity: {result.diversity_index}")
        return result

    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for analysis based on the active NLP engine"""
        logging.debug(f"Preprocessing text using engine: {self.active_nlp_engine}")
        # Truncate based on character count as an initial safeguard against extremely long texts
        # This limit should be generous enough not to interfere with max_tokens unless text is huge
        safe_text = text[:self.max_tokens * 15] # Allow ~15 chars per token average initially

        tokens = []
        try:
            # --- spaCy ---
            if self.active_nlp_engine == 'spacy' and self.nlp:
                # Process with spaCy - disable components not needed for faster processing
                # Adjust max_length if needed, default is 1,000,000
                # self.nlp.max_length = len(safe_text) + 100 # Or a higher fixed limit
                doc = self.nlp(safe_text, disable=["parser", "ner"])
                tokens = [token.lemma_.lower() for token in doc
                         if not token.is_punct and not token.is_space and not token.is_stop]

            # --- NLTK ---
            elif self.active_nlp_engine == 'nltk':
                 # Ensure NLTK resources are actually available before using
                if NLTK_AVAILABLE and nltk_ready:
                    tokens_raw = word_tokenize(safe_text.lower())
                    try:
                        stop_words = set(stopwords.words('english'))
                        tokens = [token for token in tokens_raw
                                if token.isalnum() and token not in stop_words]
                    except LookupError:
                         logging.warning("NLTK stopwords not found during preprocessing, skipping stopword removal.")
                         tokens = [token for token in tokens_raw if token.isalnum()]
                else:
                     logging.warning("NLTK selected but unavailable/resources missing, falling back to basic preprocessing.")
                     self.active_nlp_engine = 'basic' # Force basic for next step

            # --- Basic (Fallback) ---
            if self.active_nlp_engine == 'basic' or not tokens: # Fallback if other methods failed or produced no tokens
                 if self.active_nlp_engine != 'basic': # Log only if falling back unexpectedly
                      logging.warning(f"Preprocessing with {self.active_nlp_engine} failed or yielded no tokens. Falling back to basic regex tokenization.")
                 tokens = re.findall(r'\b\w+\b', safe_text.lower()) # Find word boundaries

        except Exception as e:
            logging.error(f"Error during preprocessing with {self.active_nlp_engine}: {e}. Falling back to basic.", exc_info=True)
            # Ensure fallback to basic if any error occurs
            tokens = re.findall(r'\b\w+\b', safe_text.lower())

        # Apply final max_tokens limit
        final_tokens = tokens[:self.max_tokens]
        if len(tokens) > self.max_tokens:
             logging.warning(f"Text exceeded max_tokens ({self.max_tokens}). Truncated.")

        logging.debug(f"Preprocessing resulted in {len(final_tokens)} tokens.")
        return final_tokens


    def _calculate_bias_score(self, text: str, tokens: List[str]) -> float:
        """ Calculate bias score (0-10). Higher score suggests more potential bias markers or imbalance."""
        if not tokens: return 0.0 # No tokens, no bias calculated

        bias_score = 0.0
        token_set = set(tokens)
        text_lower = text.lower()

        # Component 1: Bias Markers (Score 0-5)
        bias_markers_count = 0
        total_possible_markers = 0
        for tradition_data in self.ethical_frameworks.values():
            markers = tradition_data.get("bias_markers", [])
            total_possible_markers += len(markers)
            for marker in markers:
                # Check token set for single words, text_lower for potential phrases
                if marker in token_set or marker in text_lower:
                    bias_markers_count += 1

        if total_possible_markers > 0:
            # Normalize count relative to total markers defined across all traditions
            # Scale more generously: finding even a few markers can be significant
            marker_score = min(5.0, (bias_markers_count / total_possible_markers) * 15.0) # Amplified scale
            bias_score += marker_score
            logging.debug(f"Bias Markers Found: {bias_markers_count}/{total_possible_markers}. Score Component: {marker_score:.2f}")

        # Component 2: Ethical Framework Imbalance (Score 0-5)
        framework_scores = [self._calculate_ethics_score(trad, text, tokens) for trad in self.traditions]
        if len(framework_scores) > 1:
            # Use standard deviation as imbalance measure. Max possible std dev is 5 (half 10s, half 0s).
            imbalance_std = np.std(framework_scores)
            # Std dev is already on a reasonable scale (0-5 theoretically). Cap at 5.
            imbalance_score = min(5.0, imbalance_std)
            bias_score += imbalance_score
            logging.debug(f"Ethical Framework Scores: {[round(s, 1) for s in framework_scores]}. Imbalance (StdDev): {imbalance_std:.2f}. Score Component: {imbalance_score:.2f}")

        final_bias_score = min(10.0, bias_score) # Ensure score capped at 10
        logging.debug(f"Final Calculated Bias Score: {final_bias_score:.2f}")
        return final_bias_score


    def _calculate_diversity_index(self, text: str, tokens: List[str]) -> float:
        """ Calculate diversity index (0-10) using Shannon index for cultural and demographic representation."""
        if not tokens: return 0.0

        diversity_score = 0.0
        token_set = set(tokens)
        text_lower = text.lower()

        # Helper for normalized Shannon calculation (0-1 scale)
        def calculate_normalized_shannon(counts_dict):
            # Filter out items with zero counts before calculation
            active_counts = {k: v for k, v in counts_dict.items() if v > 0}
            num_active_groups = len(active_counts)
            total_items = sum(active_counts.values())

            if total_items == 0 or num_active_groups <= 1:
                return 0.0 # No diversity if 0 or 1 group present

            proportions = [count / total_items for count in active_counts.values()]
            shannon_index = -sum(p * np.log(p) for p in proportions if p > 0) # Ensure p > 0 for log

            # Normalize by max possible entropy for the number of *active* groups found
            max_shannon = np.log(num_active_groups)
            return (shannon_index / max_shannon) if max_shannon > 0 else 0.0

        # 1. Cultural Diversity (Score 0-5)
        cultural_counts = {}
        for culture, markers in self.cultural_markers.items():
            count = sum(1 for marker in markers if marker in token_set or marker in text_lower)
            cultural_counts[culture] = count

        cultural_diversity_norm = calculate_normalized_shannon(cultural_counts)
        diversity_score += cultural_diversity_norm * 5.0
        logging.debug(f"Cultural Diversity Score Component: {cultural_diversity_norm * 5.0:.2f} (Norm Shannon: {cultural_diversity_norm:.3f})")

        # 2. Demographic Diversity (Score 0-5)
        demographic_shannon_scores = []
        for category, groups in self.demographic_markers.items():
            group_counts = {}
            for group, markers in groups.items():
                 count = sum(1 for marker in markers if marker in token_set or marker in text_lower)
                 group_counts[group] = count

            category_shannon_norm = calculate_normalized_shannon(group_counts)
            demographic_shannon_scores.append(category_shannon_norm)
            logging.debug(f"Demographic Category '{category}' Norm Shannon: {category_shannon_norm:.3f}")

        # Average normalized Shannon scores across demographic categories
        if demographic_shannon_scores:
            avg_demographic_diversity = sum(demographic_shannon_scores) / len(demographic_shannon_scores)
            diversity_score += avg_demographic_diversity * 5.0
            logging.debug(f"Demographic Diversity Score Component: {avg_demographic_diversity * 5.0:.2f} (Avg Norm Shannon: {avg_demographic_diversity:.3f})")

        final_diversity_score = min(10.0, diversity_score) # Cap final score at 10
        logging.debug(f"Final Calculated Diversity Index: {final_diversity_score:.2f}")
        return final_diversity_score


    def _calculate_ethics_score(self, tradition: str, text: str, tokens: List[str]) -> float:
        """ Calculate alignment score (0-10) with a specific ethical tradition based on keywords."""
        if not tokens or tradition not in self.ethical_frameworks:
            return 0.0

        framework = self.ethical_frameworks[tradition]
        keywords = framework.get("keywords", [])
        if not keywords: return 0.0

        token_set = set(tokens)
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in keywords if keyword in token_set or keyword in text_lower)

        score = (keyword_count / len(keywords)) * 10.0
        logging.debug(f"Ethics Score for '{tradition}': {score:.2f} ({keyword_count}/{len(keywords)} keywords found)")
        return score


    def _identify_cultural_markers(self, text: str, tokens: List[str]) -> Dict[str, float]:
        """ Identify relative frequency of cultural markers."""
        if not tokens: return {culture: 0.0 for culture in self.cultural_markers}

        markers = {}
        total_markers_found = 0
        token_set = set(tokens)
        text_lower = text.lower()

        for culture, marker_list in self.cultural_markers.items():
            count = sum(1 for marker in marker_list if marker in token_set or marker in text_lower)
            markers[culture] = count
            total_markers_found += count

        # Normalize to percentages based on total markers FOUND
        if total_markers_found > 0:
             normalized_markers = {culture: count / total_markers_found for culture, count in markers.items()}
        else: # If no markers found, return 0 for all
             normalized_markers = {culture: 0.0 for culture in markers}

        logging.debug(f"Cultural Markers (Raw Counts): {markers}")
        logging.debug(f"Cultural Markers (Normalized): { {k: round(v, 3) for k, v in normalized_markers.items()} }")
        return normalized_markers


    def _analyze_demographics(self, text: str, tokens: List[str]) -> Dict[str, float]:
        """ Analyze relative frequency of demographic markers within their categories."""
        if not tokens: return {f"{cat}_{grp}": 0.0 for cat, groups in self.demographic_markers.items() for grp in groups}

        result = {}
        token_set = set(tokens)
        text_lower = text.lower()

        for category, groups in self.demographic_markers.items():
            category_counts = {}
            total_category_count = 0
            logging.debug(f"Analyzing Demographics for Category: {category}")

            for group, markers in groups.items():
                count = sum(1 for marker in markers if marker in token_set or marker in text_lower)
                category_counts[group] = count
                total_category_count += count
                logging.debug(f"  Group '{group}': Count={count}")

            # Normalize within the category
            if total_category_count > 0:
                for group, count in category_counts.items():
                    result[f"{category}_{group}"] = count / total_category_count
            else: # If no markers for this category, assign 0.0 to all groups
                for group in category_counts:
                     result[f"{category}_{group}"] = 0.0
            logging.debug(f"  Category '{category}' Normalized: {{ {', '.join([f'{k}: {v:.3f}' for k,v in result.items() if k.startswith(category)])} }}")

        return result


    def _extract_metadata(self, text: str, tokens: List[str]) -> Dict[str, Any]:
        """ Extract basic metadata and perform sentiment analysis if available."""
        word_count = len(tokens) # Use token count after preprocessing

        metadata = {
            "length_chars": len(text),
            "word_count": word_count,
            "sentence_count": 0, # Initialize
            "unique_words_approx": len(set(tokens)),
            "sentiment": "N/A",
            "sentiment_score": 0.0
        }

        # Sentence count using NLTK if available, otherwise basic regex
        if NLTK_AVAILABLE and nltk_ready:
            try:
                sentences = sent_tokenize(text)
                metadata["sentence_count"] = len(sentences)
            except Exception as e:
                 logging.warning(f"NLTK sent_tokenize failed: {e}. Using basic sentence split.", exc_info=True)
                 sentences_basic = re.split(r'[.!?]+', text)
                 metadata["sentence_count"] = len([s for s in sentences_basic if s.strip()]) # Count non-empty splits
        else: # Basic regex split if NLTK not available/ready
            sentences_basic = re.split(r'[.!?]+', text)
            metadata["sentence_count"] = len([s for s in sentences_basic if s.strip()])

        # Sentiment analysis using Transformers if available and loaded
        if self.sentiment_analyzer:
            try:
                # Models often have token limits (e.g., 512 for BERT types)
                # Analyze a truncated version for sentiment
                # Use tokenizer's max length if possible, otherwise default to 510/512
                max_sentiment_len = getattr(self.sentiment_analyzer.tokenizer, 'model_max_length', 512) - 2 # Account for special tokens
                sentiment_input = text[:max_sentiment_len]

                # Get sentiment - might return list even for single input
                sentiment_result = self.sentiment_analyzer(sentiment_input)

                if sentiment_result and isinstance(sentiment_result, list):
                    sentiment = sentiment_result[0] # Take the first result
                    if isinstance(sentiment, dict) and 'label' in sentiment and 'score' in sentiment:
                        metadata["sentiment"] = sentiment["label"]
                        metadata["sentiment_score"] = round(sentiment["score"], 4)
                        logging.debug(f"Sentiment Analysis Result: {metadata['sentiment']} (Score: {metadata['sentiment_score']})")
                    else:
                         logging.warning(f"Unexpected sentiment result format: {sentiment}")
                else:
                     logging.warning(f"Unexpected or empty sentiment result: {sentiment_result}")

            except Exception as e:
                logging.error(f"Error during sentiment analysis: {e}", exc_info=True)
                metadata["sentiment"] = "Error"
        else:
             logging.debug("Sentiment analyzer not available or not loaded.")


        logging.debug(f"Extracted Metadata: {metadata}")
        return metadata

    def batch_analyze(self, texts: List[str]) -> List[TextAnalysisResult]:
        """ Analyze multiple texts, processing them individually but managing flow."""
        results = []
        total_texts = len(texts)
        if total_texts == 0:
             return []

        logging.info(f"Starting batch analysis for {total_texts} texts...")

        # Simple batching loop - process one by one
        # More advanced batching (e.g., spaCy's nlp.pipe) would require restructuring
        # _analyze_text to work with pre-processed docs or integrating steps differently.
        for i, text in enumerate(texts):
            if (i + 1) % self.batch_size == 0 or (i + 1) == total_texts:
                logging.info(f"Processing text {i + 1}/{total_texts}...")
            else:
                 logging.debug(f"Processing text {i + 1}/{total_texts}...")

            try:
                 result = self._analyze_text(text)
                 results.append(result)
            except Exception as e:
                 logging.error(f"Error analyzing text at index {i}: {e}. Skipping this text.", exc_info=True)
                 # Optionally append a placeholder or None for failed texts
                 # results.append(None) # Or some error indicator object

        logging.info(f"Batch analysis complete. Processed {len(results)}/{total_texts} texts.")
        return results

# === Example Usage ===
if __name__ == "__main__":
    print("\n" + "="*20 + " Initializing TextAnalyzer " + "="*20)
    # --- Configuration ---
    # Set use_transformers=True if you have installed:
    # pip install transformers torch # or tensorflow
    # Adjust log level for more/less detail (e.g., logging.DEBUG for very verbose)
    logging.getLogger().setLevel(logging.INFO)
    USE_TRANSFORMERS_FOR_SENTIMENT = False # << Set to True to enable sentiment analysis

    analyzer = TextAnalyzer(
        use_transformers=USE_TRANSFORMERS_FOR_SENTIMENT,
        # nlp_engine='nltk', # Force NLTK (example)
        # nlp_engine='basic', # Force basic (example)
    )
    print("="*20 + " TextAnalyzer Initialized " + "="*20)

    # --- Analyze Single Text ---
    print("\nAnalyzing example text...")
    text1 = """
    In our globalized society, balancing individual rights, a cornerstone of Western
    thought (emphasizing liberty and consent), with community responsibilities is crucial.
    Ubuntu ethics powerfully reminds us 'I am because we are,' highlighting interdependence.
    Meanwhile, Confucian ideals stress social harmony and filial respect within structured hierarchies.
    Islamic principles advocate for justice (adl) and compassion (rahmah) universally.
    However, some view traditional approaches as primitive or undeveloped, a clear bias.
    The modern man seeks autonomy, while she argues for fairness. They promote sharing.
    We must avoid simplistic, exotic stereotypes when discussing different cultures.
    """
    result1 = analyzer.analyze(text1)

    print("\n--- Analysis Result (Single Text) ---")
    if result1:
        # *** CORRECT USAGE FOR JSON ***
        result_dict = result1.to_dict() # Convert to dictionary first!
        print(json.dumps(result_dict, indent=2))
    else:
        print("Analysis failed for the single text.")
    print("--- End of Single Text Analysis ---")


    # --- Analyze List of Texts (Batch) ---
    print("\nAnalyzing a list of texts (batch)...")
    text_list = [
        "Focusing solely on individual achievement can neglect community needs. This is a potential western bias.",
        "Ubuntu philosophy emphasizes our deep interconnectedness and shared humanity.",
        "He respects his elders and performs rituals, following Confucian tradition.",
        "The company needs greater accountability and transparency in its operations.",
        "Calling ancient wisdom 'primitive' compared to 'modern' solutions reveals bias.", # Contains bias markers
        "She works hard. The child plays happily. The senior citizen rests peacefully.", # Contains demographic markers
        "", # Empty string example
        "This text mentions Europe, Africa, China, and India, reflecting geographic diversity." # Cultural markers
    ]
    list_results = analyzer.analyze(text_list) # analyzer.analyze handles lists directly

    print(f"\n--- Batch Analysis Results ({len(list_results)} texts processed) ---")
    if list_results:
        # *** CORRECT USAGE FOR JSON ***
        list_of_dicts = [res.to_dict() for res in list_results if res] # Convert each valid result to dict
        print(json.dumps(list_of_dicts, indent=2))

        # Or print individually:
        # for i, res in enumerate(list_results):
        #     print(f"\n--- Result for Text {i+1} ---")
        #     if res:
        #         print(json.dumps(res.to_dict(), indent=2))
        #     else:
        #         print("Analysis failed or skipped for this text.")
    else:
         print("Batch analysis failed or returned no results.")
    print("--- End of Batch Analysis ---")


    # --- Analyze from File (Example) ---
    # Create dummy files first if they don't exist
    DUMMY_TXT_FILE = "temp_analysis_test.txt"
    DUMMY_CSV_FILE = "temp_analysis_test.csv"
    DUMMY_JSON_FILE = "temp_analysis_test.json"

    print(f"\nAttempting file analysis examples (using temporary files)...")
    try:
        # Create dummy .txt
        with open(DUMMY_TXT_FILE, "w", encoding="utf-8") as f:
            f.write("This is text from a file. It mentions America and European ideas. Also mentions community from Africa.")
        print(f"\n--- Analyzing {DUMMY_TXT_FILE} ---")
        file_result_txt = analyzer.analyze(DUMMY_TXT_FILE)
        if file_result_txt:
            print(json.dumps(file_result_txt.to_dict(), indent=2)) # Use .to_dict()
        else:
            print(f"Analysis failed for {DUMMY_TXT_FILE}")

        # Create dummy .csv
        df_data = {'text': ["CSV Row 1: Focus on individual rights.", "CSV Row 2: Mentioning ubuntu and harmony."], 'other_col': [1, 2]}
        pd.DataFrame(df_data).to_csv(DUMMY_CSV_FILE, index=False)
        print(f"\n--- Analyzing {DUMMY_CSV_FILE} ---")
        file_results_csv = analyzer.analyze(DUMMY_CSV_FILE)
        if file_results_csv:
            print(json.dumps([res.to_dict() for res in file_results_csv], indent=2)) # Use .to_dict() in list comprehension
        else:
            print(f"Analysis failed for {DUMMY_CSV_FILE}")


        # Create dummy .json (list of dicts)
        json_data = [{'text': "JSON object 1: Discussing Confucian ethics like filial piety."}, {'text': "JSON object 2: Islamic justice and charity."}]
        with open(DUMMY_JSON_FILE, "w", encoding="utf-8") as f:
             json.dump(json_data, f, indent=2)
        print(f"\n--- Analyzing {DUMMY_JSON_FILE} ---")
        file_results_json = analyzer.analyze(DUMMY_JSON_FILE)
        if file_results_json:
             print(json.dumps([res.to_dict() for res in file_results_json], indent=2)) # Use .to_dict()
        else:
             print(f"Analysis failed for {DUMMY_JSON_FILE}")


    except Exception as e:
        print(f"\nFile analysis example encountered an error: {e}")
    finally:
        # Clean up dummy files
        for fpath in [DUMMY_TXT_FILE, DUMMY_CSV_FILE, DUMMY_JSON_FILE]:
             if os.path.exists(fpath):
                  try:
                       os.remove(fpath)
                       print(f"Cleaned up temporary file: {fpath}")
                  except OSError as oe:
                       print(f"Warning: Could not remove temporary file {fpath}: {oe}")

    print("\n" + "="*20 + " Example Usage Finished " + "="*20)