"""Enhanced ICD-10 disease prediction model with comprehensive patient analysis."""

import json
import pickle
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Try to import ML model for enhanced predictions
try:
    from .ml_model import ICDMLModel, MLModelError
    ML_MODEL_AVAILABLE = True
except ImportError:
    ML_MODEL_AVAILABLE = False
    logger.info("ML model not available, using rule-based predictions only")


class PatientValidationError(ValueError):
    """Custom exception for patient data validation errors."""
    pass


class PredictorDataError(Exception):
    """Custom exception for predictor data loading errors."""
    pass


# Validation constants
VALID_SEX_VALUES = ['M', 'F', 'MALE', 'FEMALE']
AGE_MIN = 0
AGE_MAX = 150
HEIGHT_MIN = 20  # cm (smallest recorded human)
HEIGHT_MAX = 280  # cm (tallest recorded human)
WEIGHT_MIN = 0.5  # kg (premature infant)
WEIGHT_MAX = 700  # kg (heaviest recorded human)
BP_SYSTOLIC_MIN = 50
BP_SYSTOLIC_MAX = 300
BP_DIASTOLIC_MIN = 30
BP_DIASTOLIC_MAX = 200
HEART_RATE_MIN = 20
HEART_RATE_MAX = 300
TEMPERATURE_MIN = 25.0  # Celsius (severe hypothermia)
TEMPERATURE_MAX = 45.0  # Celsius (severe hyperthermia)
RESPIRATORY_RATE_MIN = 5
RESPIRATORY_RATE_MAX = 60


def validate_range(value: Any, min_val: float, max_val: float, field_name: str) -> None:
    """Validate that a numeric value is within the specified range."""
    if value is not None:
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise PatientValidationError(f"{field_name} must be a valid number, got {value}")
        
        if num_value < min_val or num_value > max_val:
            raise PatientValidationError(
                f"{field_name} must be between {min_val} and {max_val}, got {value}"
            )


@dataclass
class PatientDetails:
    """Patient information for disease prediction."""
    age: int
    sex: str  # 'M' or 'F'
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    respiratory_rate: Optional[int] = None
    symptoms: List[str] = field(default_factory=list)
    primary_complaints: List[str] = field(default_factory=list)
    medical_history: List[str] = field(default_factory=list)
    comorbidities: List[str] = field(default_factory=list)
    doctor_specialty: Optional[str] = None
    
    def __post_init__(self):
        # Initialize empty lists if None
        if self.symptoms is None:
            self.symptoms = []
        if self.primary_complaints is None:
            self.primary_complaints = []
        if self.medical_history is None:
            self.medical_history = []
        if self.comorbidities is None:
            self.comorbidities = []
        
        # Validate and normalize sex
        if not self.sex:
            raise PatientValidationError("Sex is required")
        
        self.sex = str(self.sex).strip().upper()
        if self.sex not in VALID_SEX_VALUES:
            raise PatientValidationError(
                f"Sex must be one of {VALID_SEX_VALUES}, got '{self.sex}'"
            )
        # Normalize to single character
        self.sex = 'M' if self.sex in ['M', 'MALE'] else 'F'
        
        # Validate age
        validate_range(self.age, AGE_MIN, AGE_MAX, "Age")
        
        # Validate vitals if provided
        validate_range(self.height_cm, HEIGHT_MIN, HEIGHT_MAX, "Height")
        validate_range(self.weight_kg, WEIGHT_MIN, WEIGHT_MAX, "Weight")
        validate_range(self.systolic_bp, BP_SYSTOLIC_MIN, BP_SYSTOLIC_MAX, "Systolic BP")
        validate_range(self.diastolic_bp, BP_DIASTOLIC_MIN, BP_DIASTOLIC_MAX, "Diastolic BP")
        validate_range(self.heart_rate, HEART_RATE_MIN, HEART_RATE_MAX, "Heart rate")
        validate_range(self.temperature_c, TEMPERATURE_MIN, TEMPERATURE_MAX, "Temperature")
        validate_range(self.respiratory_rate, RESPIRATORY_RATE_MIN, RESPIRATORY_RATE_MAX, "Respiratory rate")
        
        # Validate BP consistency
        if self.systolic_bp is not None and self.diastolic_bp is not None:
            if self.diastolic_bp >= self.systolic_bp:
                raise PatientValidationError(
                    f"Diastolic BP ({self.diastolic_bp}) must be less than systolic BP ({self.systolic_bp})"
                )
        
        # Sanitize string lists
        self.symptoms = self._sanitize_string_list(self.symptoms, "symptoms")
        self.primary_complaints = self._sanitize_string_list(self.primary_complaints, "primary_complaints")
        self.medical_history = self._sanitize_string_list(self.medical_history, "medical_history")
        self.comorbidities = self._sanitize_string_list(self.comorbidities, "comorbidities")
        
        logger.debug(f"Created PatientDetails: age={self.age}, sex={self.sex}, symptoms={len(self.symptoms)}")
    
    def _sanitize_string_list(self, items: List[str], field_name: str) -> List[str]:
        """Sanitize a list of strings by stripping whitespace and removing empty items."""
        if not isinstance(items, list):
            raise PatientValidationError(f"{field_name} must be a list")
        
        sanitized = []
        for item in items:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:  # Only add non-empty strings
                    sanitized.append(cleaned)
            else:
                logger.warning(f"Skipping non-string item in {field_name}: {item}")
        
        return sanitized
    
    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI if height and weight are available."""
        if self.height_cm and self.weight_kg:
            try:
                if self.height_cm <= 0:
                    logger.warning("Cannot calculate BMI: height is zero or negative")
                    return None
                height_m = self.height_cm / 100
                bmi_value = self.weight_kg / (height_m ** 2)
                return round(bmi_value, 2)
            except (ZeroDivisionError, TypeError) as e:
                logger.warning(f"Failed to calculate BMI: {e}")
                return None
        return None
    
    @property
    def bmi_category(self) -> Optional[str]:
        """Categorize BMI."""
        bmi = self.bmi
        if bmi is None:
            return None
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    
    @property
    def bp_category(self) -> Optional[str]:
        """Categorize blood pressure."""
        if self.systolic_bp is None or self.diastolic_bp is None:
            return None
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "Normal"
        elif self.systolic_bp < 130 and self.diastolic_bp < 80:
            return "Elevated"
        elif self.systolic_bp < 140 or self.diastolic_bp < 90:
            return "Stage 1 Hypertension"
        else:
            return "Stage 2 Hypertension"
    
    @property
    def specialty(self) -> Optional[str]:
        """Alias for doctor_specialty for convenience."""
        return self.doctor_specialty


@dataclass
class ICDPrediction:
    """ICD code prediction result."""
    code: str
    description: str
    probability_score: float
    matched_symptoms: List[str]
    related_vitals: Dict[str, str]
    confidence_level: str  # 'High', 'Medium', 'Low'
    matching_explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'icd_code': self.code,
            'description': self.description,
            'probability_score': round(self.probability_score, 3),
            'confidence_level': self.confidence_level,
            'matched_symptoms': self.matched_symptoms,
            'related_vitals': self.related_vitals,
            'matching_explanation': self.matching_explanation
        }


class EnhancedICDPredictor:
    """Enhanced ICD-10 predictor with comprehensive patient analysis.
    
    Uses ML-based TF-IDF model when available, falling back to rule-based matching.
    """
    
    def __init__(self, data_dir: str = None, use_ml: bool = True):
        """Initialize predictor with data files.
        
        Args:
            data_dir: Directory containing icd_list.json and counts.pickle
            use_ml: Whether to use ML model for enhanced predictions (default: True)
            
        Raises:
            PredictorDataError: If required data files cannot be loaded
        """
        if data_dir is None:
            data_dir = str(Path(__file__).parent.parent.parent)
        
        self.data_dir = Path(data_dir)
        self.use_ml = use_ml and ML_MODEL_AVAILABLE
        self.ml_model: Optional[ICDMLModel] = None
        
        logger.info(f"Initializing EnhancedICDPredictor with data_dir: {self.data_dir}")
        
        try:
            self.icd_list = self._load_icd_list()
            self.counts = self._load_counts()
            logger.info(f"Predictor initialized with {len(self.icd_list)} ICD codes")
            
            # Initialize ML model if enabled
            if self.use_ml:
                try:
                    self.ml_model = ICDMLModel(data_dir=str(self.data_dir))
                    logger.info("ML model initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize ML model, falling back to rule-based: {e}")
                    self.ml_model = None
                    self.use_ml = False
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            raise PredictorDataError(f"Failed to initialize predictor: {e}")
        
    def _load_icd_list(self) -> List[Dict[str, str]]:
        """Load and parse ICD-10 code list.
        
        Returns:
            List of dictionaries with 'description' and 'code' keys
            
        Raises:
            PredictorDataError: If file cannot be loaded or parsed
        """
        icd_file = self.data_dir / 'icd_list.json'
        
        if not icd_file.exists():
            raise PredictorDataError(f"ICD list not found at {icd_file}")
        
        try:
            with open(icd_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
        except json.JSONDecodeError as e:
            raise PredictorDataError(f"Invalid JSON in ICD list file: {e}")
        except IOError as e:
            raise PredictorDataError(f"Failed to read ICD list file: {e}")
        
        if not isinstance(raw_list, list):
            raise PredictorDataError("ICD list file must contain a JSON array")
        
        parsed_list = []
        parse_errors = 0
        
        for i, entry in enumerate(raw_list):
            if not isinstance(entry, str):
                logger.warning(f"Skipping non-string entry at index {i}: {type(entry)}")
                parse_errors += 1
                continue
                
            if ':' not in entry:
                logger.warning(f"Skipping entry without colon separator at index {i}: {entry[:50]}...")
                parse_errors += 1
                continue
            
            try:
                desc, code = entry.split(':', 1)
                desc = desc.strip().lower()
                code = code.strip()
                
                if desc and code:
                    parsed_list.append({
                        'description': desc,
                        'code': code
                    })
                else:
                    parse_errors += 1
            except Exception as e:
                logger.warning(f"Failed to parse entry at index {i}: {e}")
                parse_errors += 1
        
        if parse_errors > 0:
            logger.warning(f"Encountered {parse_errors} parse errors while loading ICD list")
        
        if len(parsed_list) == 0:
            raise PredictorDataError("No valid ICD entries found in file")
        
        logger.info(f"Loaded {len(parsed_list)} ICD codes from {icd_file}")
        return parsed_list
    
    def _load_counts(self) -> Dict:
        """Load historical diagnosis counts.
        
        Returns:
            Dictionary of diagnosis counts, or empty dict if file doesn't exist
        """
        counts_file = self.data_dir / 'counts.pickle'
        
        if not counts_file.exists():
            logger.warning(f"Counts file not found at {counts_file}, using empty counts")
            return {}
        
        try:
            with open(counts_file, 'rb') as f:
                counts = pickle.load(f)
                logger.info(f"Loaded counts data with {len(counts)} entries")
                return counts
        except (pickle.UnpicklingError, EOFError) as e:
            logger.error(f"Failed to unpickle counts file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading counts: {e}")
            return {}
    
    def _calculate_base_probability(self, patient: PatientDetails, code: str) -> float:
        """Calculate base probability from historical data."""
        key = (str(patient.age), patient.sex, 
               patient.doctor_specialty.upper() if patient.doctor_specialty else 'GENERAL')
        
        if key in self.counts:
            code_freq = dict(self.counts[key])
            if code in code_freq:
                total = sum(code_freq.values())
                return code_freq[code] / total
        
        return 0.1  # Base probability for unknown combinations
    
    def _match_symptoms_to_description(self, symptoms: List[str], description: str) -> Tuple[List[str], float]:
        """Match patient symptoms to disease description."""
        matched = []
        desc_lower = description.lower()
        
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            # Check for exact match or partial match
            if symptom_lower in desc_lower or any(word in desc_lower for word in symptom_lower.split()):
                matched.append(symptom)
        
        # Calculate symptom match score
        if len(symptoms) > 0:
            match_score = len(matched) / len(symptoms)
        else:
            match_score = 0.0
        
        return matched, match_score
    
    def _analyze_vitals_relevance(self, patient: PatientDetails, description: str) -> Dict[str, str]:
        """Analyze which vitals are relevant to the condition."""
        relevant = {}
        desc_lower = description.lower()
        
        # Check BMI relevance
        if patient.bmi and any(term in desc_lower for term in ['weight', 'obesity', 'overweight', 'bmi', 'underweight']):
            relevant['bmi'] = f"{patient.bmi} ({patient.bmi_category})"
        
        # Check BP relevance
        if patient.systolic_bp and any(term in desc_lower for term in ['hypertension', 'blood pressure', 'bp', 'hypotension']):
            relevant['blood_pressure'] = f"{patient.systolic_bp}/{patient.diastolic_bp} mmHg ({patient.bp_category})"
        
        # Check temperature relevance
        if patient.temperature_c and any(term in desc_lower for term in ['fever', 'temperature', 'pyrexia', 'hypothermia']):
            status = 'Elevated' if patient.temperature_c > 37.5 else 'Normal'
            relevant['temperature'] = f"{patient.temperature_c}°C ({status})"
        
        # Check heart rate relevance
        if patient.heart_rate and any(term in desc_lower for term in ['heart', 'cardiac', 'tachycardia', 'bradycardia']):
            if patient.heart_rate > 100:
                status = 'Tachycardia'
            elif patient.heart_rate < 60:
                status = 'Bradycardia'
            else:
                status = 'Normal'
            relevant['heart_rate'] = f"{patient.heart_rate} bpm ({status})"
        
        # Check respiratory rate relevance
        if patient.respiratory_rate and any(term in desc_lower for term in ['respiratory', 'breathing', 'dyspnea', 'tachypnea']):
            status = 'Elevated' if patient.respiratory_rate > 20 else 'Normal'
            relevant['respiratory_rate'] = f"{patient.respiratory_rate} breaths/min ({status})"
        
        return relevant
    
    def _generate_matching_explanation(self, patient: PatientDetails, prediction: Dict, 
                                       matched_symptoms: List[str], symptom_score: float,
                                       vitals_relevance: Dict[str, str]) -> str:
        """Generate detailed explanation of how patient matches the condition."""
        explanation_parts = []
        
        # Symptom matching
        if matched_symptoms:
            explanation_parts.append(
                f"Matched {len(matched_symptoms)} of {len(patient.symptoms)} reported symptoms: {', '.join(matched_symptoms)}."
            )
        else:
            explanation_parts.append("No direct symptom matches found in the description.")
        
        # Vitals analysis
        if vitals_relevance:
            vital_descriptions = [f"{k}: {v}" for k, v in vitals_relevance.items()]
            explanation_parts.append(
                f"Relevant vital signs: {'; '.join(vital_descriptions)}."
            )
        
        # Comorbidities
        if patient.comorbidities:
            explanation_parts.append(
                f"Patient has comorbidities: {', '.join(patient.comorbidities)}."
            )
        
        # Medical history
        if patient.medical_history:
            explanation_parts.append(
                f"Medical history includes: {', '.join(patient.medical_history)}."
            )
        
        # Demographics
        demo = f"Patient demographics: {patient.age} years old, {patient.sex}"
        if patient.bmi:
            demo += f", BMI {patient.bmi}"
        explanation_parts.append(demo + ".")
        
        return " ".join(explanation_parts)
    
    def predict(self, patient: PatientDetails, top_n: int = 10) -> List[ICDPrediction]:
        """
        Predict ICD codes for patient with comprehensive analysis.
        
        Uses ML-based TF-IDF model when available for enhanced accuracy,
        falling back to rule-based matching otherwise.
        
        Args:
            patient: Patient details
            top_n: Number of top predictions to return (1-100)
            
        Returns:
            List of ICD predictions sorted by probability score
            
        Raises:
            PatientValidationError: If patient data is invalid
            ValueError: If top_n is out of range
        """
        # Validate inputs
        if not isinstance(patient, PatientDetails):
            raise PatientValidationError("patient must be a PatientDetails instance")
        
        if not isinstance(top_n, int) or top_n < 1:
            raise ValueError("top_n must be a positive integer")
        
        if top_n > 100:
            logger.warning(f"top_n ({top_n}) exceeds maximum of 100, capping at 100")
            top_n = 100
        
        logger.info(f"Predicting ICD codes for patient (age={patient.age}, sex={patient.sex}, symptoms={len(patient.symptoms)})")
        
        all_symptoms = patient.symptoms + patient.primary_complaints
        
        # Use ML model if available for better predictions
        if self.ml_model is not None and all_symptoms:
            return self._predict_ml(patient, all_symptoms, top_n)
        
        # Fall back to rule-based prediction
        return self._predict_rule_based(patient, all_symptoms, top_n)
    
    def _predict_ml(self, patient: PatientDetails, all_symptoms: List[str], top_n: int) -> List[ICDPrediction]:
        """Use ML model for predictions.
        
        Args:
            patient: Patient details
            all_symptoms: Combined symptoms and complaints
            top_n: Number of predictions to return
            
        Returns:
            List of ICDPrediction objects
        """
        logger.info("Using ML model for predictions")
        
        # Prepare vitals dictionary
        vitals = {}
        if patient.bmi:
            vitals['bmi'] = patient.bmi
            vitals['bmi_category'] = patient.bmi_category
        if patient.systolic_bp:
            vitals['systolic_bp'] = patient.systolic_bp
            vitals['diastolic_bp'] = patient.diastolic_bp
            vitals['bp_category'] = patient.bp_category
        if patient.temperature_c:
            vitals['temperature'] = patient.temperature_c
        if patient.heart_rate:
            vitals['heart_rate'] = patient.heart_rate
        if patient.respiratory_rate:
            vitals['respiratory_rate'] = patient.respiratory_rate
        
        # Get ML predictions
        ml_predictions = self.ml_model.predict(
            symptoms=all_symptoms,
            age=patient.age,
            sex=patient.sex,
            specialty=patient.specialty,
            vitals=vitals,
            top_n=top_n
        )
        
        # Convert to ICDPrediction objects
        predictions = []
        for ml_pred in ml_predictions:
            # Get vitals relevance using our method
            vitals_relevance = self._analyze_vitals_relevance(patient, ml_pred['description'])
            
            # Get matched symptoms
            matched_symptoms = ml_pred.get('matched_symptoms', [])
            
            # Get scores from nested structure
            scores = ml_pred.get('scores', {})
            tfidf_score = scores.get('tfidf_similarity', 0.0)
            historical_score = scores.get('historical_probability', 0.0)
            vitals_boost = scores.get('vitals_relevance', 0.0)
            
            # Use ML-generated explanation as base
            explanation = ml_pred.get('matching_explanation', '')
            
            # Add ML scoring info to explanation
            ml_explanation = f" [ML Score: TF-IDF={tfidf_score:.3f}"
            if historical_score > 0:
                ml_explanation += f", Historical={historical_score:.3f}"
            if vitals_boost > 0:
                ml_explanation += f", Vitals={vitals_boost:.3f}"
            ml_explanation += "]"
            explanation += ml_explanation
            
            # Merge vitals from ML model and local analysis
            merged_vitals = {**ml_pred.get('related_vitals', {}), **vitals_relevance}
            
            predictions.append(ICDPrediction(
                code=ml_pred['code'],
                description=ml_pred['description'],
                probability_score=ml_pred['probability_score'],
                matched_symptoms=matched_symptoms,
                related_vitals=merged_vitals,
                confidence_level=ml_pred['confidence_level'],
                matching_explanation=explanation
            ))
        
        return predictions
    
    def _predict_rule_based(self, patient: PatientDetails, all_symptoms: List[str], top_n: int) -> List[ICDPrediction]:
        """Use rule-based matching for predictions.
        
        Args:
            patient: Patient details
            all_symptoms: Combined symptoms and complaints
            top_n: Number of predictions to return
            
        Returns:
            List of ICDPrediction objects
        """
        logger.info("Using rule-based predictions")
        predictions = []
        
        # Search through ICD codes
        for icd_entry in self.icd_list:
            description = icd_entry['description']
            code = icd_entry['code']
            
            # Check if any symptom matches the description
            matched_symptoms, symptom_score = self._match_symptoms_to_description(
                all_symptoms, description
            )
            
            # Skip if no symptoms match and we have symptoms
            if len(all_symptoms) > 0 and len(matched_symptoms) == 0:
                continue
            
            # Calculate probability
            base_prob = self._calculate_base_probability(patient, code)
            
            # Boost probability based on symptom matching
            probability = base_prob + (symptom_score * 0.5)
            
            # Analyze vital signs relevance
            vitals_relevance = self._analyze_vitals_relevance(patient, description)
            
            # Boost probability if vitals are relevant
            if vitals_relevance:
                probability += 0.2 * len(vitals_relevance)
            
            # Check comorbidities match
            for comorbidity in patient.comorbidities:
                if comorbidity.lower() in description:
                    probability += 0.15
            
            # Cap probability at 1.0
            probability = min(probability, 1.0)
            
            # Determine confidence level
            if probability >= 0.7:
                confidence = 'High'
            elif probability >= 0.4:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            # Generate explanation
            explanation = self._generate_matching_explanation(
                patient, icd_entry, matched_symptoms, symptom_score, vitals_relevance
            )
            
            predictions.append(ICDPrediction(
                code=code,
                description=description.capitalize(),
                probability_score=probability,
                matched_symptoms=matched_symptoms,
                related_vitals=vitals_relevance,
                confidence_level=confidence,
                matching_explanation=explanation
            ))
        
        # Sort by probability score
        predictions.sort(key=lambda x: x.probability_score, reverse=True)
        
        return predictions[:top_n]
