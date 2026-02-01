"""ML-based ICD-10 prediction model using TF-IDF and ensemble methods."""

import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)


class MLModelError(Exception):
    """Custom exception for ML model errors."""
    pass


class ICDMLModel:
    """Machine Learning model for ICD-10 code prediction.
    
    Uses TF-IDF vectorization for symptom/description matching
    combined with demographic and vital sign features.
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize the ML model.
        
        Args:
            data_dir: Directory containing icd_list.json and counts.pickle
        """
        if data_dir is None:
            data_dir = str(Path(__file__).parent.parent.parent)
        
        self.data_dir = Path(data_dir)
        self.icd_data: List[Dict[str, str]] = []
        self.descriptions: List[str] = []
        self.codes: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.historical_counts: Dict = {}
        
        self._load_data()
        self._build_model()
    
    def _load_data(self):
        """Load ICD codes and historical data."""
        # Load ICD list
        icd_file = self.data_dir / 'icd_list.json'
        if not icd_file.exists():
            raise FileNotFoundError(f"ICD list not found at {icd_file}")
        
        with open(icd_file, 'r', encoding='utf-8') as f:
            raw_list = json.load(f)
        
        for entry in raw_list:
            if ':' in entry:
                desc, code = entry.split(':', 1)
                desc = desc.strip().lower()
                code = code.strip()
                if desc and code:
                    self.icd_data.append({'description': desc, 'code': code})
                    self.descriptions.append(desc)
                    self.codes.append(code)
        
        logger.info(f"Loaded {len(self.icd_data)} ICD codes")
        
        # Load historical counts
        counts_file = self.data_dir / 'counts.pickle'
        if counts_file.exists():
            try:
                with open(counts_file, 'rb') as f:
                    self.historical_counts = pickle.load(f)
                logger.info(f"Loaded historical counts with {len(self.historical_counts)} demographic keys")
            except Exception as e:
                logger.warning(f"Could not load historical counts: {e}")
                self.historical_counts = {}
    
    def _build_model(self):
        """Build the TF-IDF vectorizer and matrix."""
        logger.info("Building TF-IDF model...")
        
        # Create TF-IDF vectorizer with medical-friendly settings
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),  # Unigrams, bigrams, and trigrams
            max_features=50000,
            stop_words='english',
            min_df=1,
            max_df=0.95,
            sublinear_tf=True  # Apply sublinear scaling
        )
        
        # Fit and transform the ICD descriptions
        self.tfidf_matrix = self.vectorizer.fit_transform(self.descriptions)
        logger.info(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
    
    def _get_age_bracket(self, age: int) -> str:
        """Convert age to bracket string matching historical data format."""
        if age < 10:
            return '0-10'
        elif age < 20:
            return '10-20'
        elif age < 30:
            return '20-30'
        elif age < 40:
            return '30-40'
        elif age < 50:
            return '40-50'
        elif age < 60:
            return '50-60'
        elif age < 70:
            return '60-70'
        elif age < 80:
            return '70-80'
        elif age < 90:
            return '80-90'
        else:
            return '90+'
    
    def _get_sex_string(self, sex: str) -> str:
        """Convert sex to format matching historical data."""
        return 'MALE' if sex.upper() in ['M', 'MALE'] else 'FEMALE'
    
    def _get_historical_probability(self, age: int, sex: str, specialty: str, code: str) -> float:
        """Get probability from historical data."""
        age_bracket = self._get_age_bracket(age)
        sex_str = self._get_sex_string(sex)
        specialty_upper = specialty.upper() if specialty else 'GENERAL'
        
        key = (age_bracket, sex_str, specialty_upper)
        
        if key in self.historical_counts:
            code_counts = dict(self.historical_counts[key])
            if code in code_counts:
                total = sum(code_counts.values())
                return code_counts[code] / total if total > 0 else 0.0
        
        return 0.0
    
    def predict(
        self,
        symptoms: List[str],
        age: int = None,
        sex: str = None,
        specialty: str = None,
        vitals: Dict[str, Any] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Predict ICD codes based on symptoms and patient info.
        
        Args:
            symptoms: List of symptom strings
            age: Patient age
            sex: Patient sex ('M' or 'F')
            specialty: Doctor specialty
            vitals: Dictionary of vital signs (bmi, bp, temp, etc.)
            top_n: Number of top predictions to return
            
        Returns:
            List of prediction dictionaries with scores and explanations
        """
        if not symptoms:
            return []
        
        # Combine symptoms into a query
        query = ' '.join(symptoms).lower()
        
        # Transform query using TF-IDF
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity with all ICD descriptions
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top candidates (more than needed for filtering)
        n_candidates = min(top_n * 5, len(similarities))
        top_indices = np.argsort(similarities)[-n_candidates:][::-1]
        
        predictions = []
        
        for idx in top_indices:
            if similarities[idx] < 0.01:  # Skip very low similarity
                continue
            
            code = self.codes[idx]
            description = self.descriptions[idx]
            
            # Base score from TF-IDF similarity
            tfidf_score = float(similarities[idx])
            
            # Historical score boost
            historical_score = 0.0
            if age is not None and sex is not None:
                historical_score = self._get_historical_probability(
                    age, sex, specialty or 'GENERAL', code
                )
            
            # Vitals relevance boost
            vitals_boost = 0.0
            vitals_matched = {}
            if vitals:
                vitals_boost, vitals_matched = self._calculate_vitals_boost(
                    description, vitals
                )
            
            # Combined score with weights
            # TF-IDF: 60%, Historical: 25%, Vitals: 15%
            combined_score = (
                0.60 * tfidf_score +
                0.25 * historical_score +
                0.15 * vitals_boost
            )
            
            # Find matched symptoms
            matched_symptoms = self._find_matched_symptoms(symptoms, description)
            
            # Determine confidence level
            if combined_score >= 0.5:
                confidence = 'High'
            elif combined_score >= 0.25:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            predictions.append({
                'code': code,
                'description': description.capitalize(),
                'probability_score': round(min(combined_score, 1.0), 4),
                'confidence_level': confidence,
                'matched_symptoms': matched_symptoms,
                'related_vitals': vitals_matched,
                'scores': {
                    'tfidf_similarity': round(tfidf_score, 4),
                    'historical_probability': round(historical_score, 4),
                    'vitals_relevance': round(vitals_boost, 4)
                },
                'matching_explanation': self._generate_explanation(
                    matched_symptoms, vitals_matched, tfidf_score, historical_score
                )
            })
        
        # Sort by combined score and return top_n
        predictions.sort(key=lambda x: x['probability_score'], reverse=True)
        return predictions[:top_n]
    
    def _calculate_vitals_boost(
        self, description: str, vitals: Dict[str, Any]
    ) -> Tuple[float, Dict[str, str]]:
        """Calculate boost score based on vital signs relevance."""
        boost = 0.0
        matched = {}
        desc_lower = description.lower()
        
        # BMI relevance
        if vitals.get('bmi'):
            bmi_terms = ['weight', 'obesity', 'overweight', 'bmi', 'underweight', 'malnutrition']
            if any(term in desc_lower for term in bmi_terms):
                boost += 0.3
                matched['bmi'] = str(vitals['bmi'])
        
        # Blood pressure relevance
        if vitals.get('systolic_bp') and vitals.get('diastolic_bp'):
            bp_terms = ['hypertension', 'blood pressure', 'hypotension', 'cardiovascular']
            if any(term in desc_lower for term in bp_terms):
                boost += 0.3
                matched['blood_pressure'] = f"{vitals['systolic_bp']}/{vitals['diastolic_bp']} mmHg"
        
        # Temperature relevance
        if vitals.get('temperature'):
            temp_terms = ['fever', 'pyrexia', 'hypothermia', 'temperature', 'febrile', 'infection']
            if any(term in desc_lower for term in temp_terms):
                boost += 0.2
                matched['temperature'] = f"{vitals['temperature']}°C"
        
        # Heart rate relevance
        if vitals.get('heart_rate'):
            hr_terms = ['tachycardia', 'bradycardia', 'heart', 'cardiac', 'arrhythmia', 'palpitation']
            if any(term in desc_lower for term in hr_terms):
                boost += 0.2
                matched['heart_rate'] = f"{vitals['heart_rate']} bpm"
        
        # Respiratory rate relevance
        if vitals.get('respiratory_rate'):
            rr_terms = ['respiratory', 'breathing', 'dyspnea', 'tachypnea', 'breath', 'pulmonary']
            if any(term in desc_lower for term in rr_terms):
                boost += 0.2
                matched['respiratory_rate'] = f"{vitals['respiratory_rate']} breaths/min"
        
        return min(boost, 1.0), matched
    
    def _find_matched_symptoms(self, symptoms: List[str], description: str) -> List[str]:
        """Find which symptoms match the ICD description."""
        matched = []
        desc_lower = description.lower()
        
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            # Check for exact match or word overlap
            symptom_words = set(symptom_lower.split())
            desc_words = set(desc_lower.split())
            
            if symptom_lower in desc_lower or len(symptom_words & desc_words) > 0:
                matched.append(symptom)
        
        return matched
    
    def _generate_explanation(
        self,
        matched_symptoms: List[str],
        vitals_matched: Dict[str, str],
        tfidf_score: float,
        historical_score: float
    ) -> str:
        """Generate human-readable explanation for the prediction."""
        parts = []
        
        if matched_symptoms:
            parts.append(f"Matched symptoms: {', '.join(matched_symptoms)}")
        
        if vitals_matched:
            vital_strs = [f"{k}: {v}" for k, v in vitals_matched.items()]
            parts.append(f"Relevant vitals: {'; '.join(vital_strs)}")
        
        if tfidf_score > 0.3:
            parts.append("Strong text similarity with condition description")
        elif tfidf_score > 0.1:
            parts.append("Moderate text similarity with condition description")
        
        if historical_score > 0.1:
            parts.append("Commonly diagnosed for similar patient demographics")
        
        return '. '.join(parts) if parts else "Based on symptom analysis"
    
    def search_by_code(self, code: str) -> Optional[Dict[str, str]]:
        """Look up an ICD code."""
        code_upper = code.upper().strip()
        for entry in self.icd_data:
            if entry['code'].upper() == code_upper:
                return {
                    'code': entry['code'],
                    'description': entry['description'].capitalize()
                }
        return None
    
    def search_by_description(self, query: str, limit: int = 20) -> List[Dict[str, str]]:
        """Search ICD codes by description using TF-IDF."""
        if not query or len(query) < 2:
            return []
        
        query_vector = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        top_indices = np.argsort(similarities)[-limit:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:
                results.append({
                    'code': self.codes[idx],
                    'description': self.descriptions[idx].capitalize(),
                    'relevance_score': round(float(similarities[idx]), 4)
                })
        
        return results


def create_ml_model(data_dir: str = None) -> ICDMLModel:
    """Factory function to create ML model instance."""
    return ICDMLModel(data_dir=data_dir)


if __name__ == '__main__':
    # Test the model
    logging.basicConfig(level=logging.INFO)
    
    model = ICDMLModel()
    
    # Test prediction
    results = model.predict(
        symptoms=['chest pain', 'shortness of breath', 'fatigue'],
        age=55,
        sex='M',
        specialty='CARDIOLOGY',
        vitals={'systolic_bp': 150, 'diastolic_bp': 95, 'heart_rate': 90},
        top_n=5
    )
    
    print("\nPrediction Results:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['code']}: {r['description']}")
        print(f"   Score: {r['probability_score']:.2%} ({r['confidence_level']})")
        print(f"   Matched: {r['matched_symptoms']}")
        print(f"   Explanation: {r['matching_explanation']}")
