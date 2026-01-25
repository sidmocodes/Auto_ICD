"""Enhanced ICD-10 disease prediction model with comprehensive patient analysis."""

import json
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


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
    symptoms: List[str] = None
    primary_complaints: List[str] = None
    medical_history: List[str] = None
    comorbidities: List[str] = None
    doctor_specialty: Optional[str] = None
    
    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []
        if self.primary_complaints is None:
            self.primary_complaints = []
        if self.medical_history is None:
            self.medical_history = []
        if self.comorbidities is None:
            self.comorbidities = []
        
        # Normalize sex
        self.sex = self.sex.upper()
        if self.sex not in ['M', 'F']:
            raise ValueError("Sex must be 'M' or 'F'")
    
    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI if height and weight are available."""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 2)
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
    """Enhanced ICD-10 predictor with comprehensive patient analysis."""
    
    def __init__(self, data_dir: str = None):
        """Initialize predictor with data files."""
        if data_dir is None:
            data_dir = str(Path(__file__).parent.parent.parent)
        
        self.data_dir = Path(data_dir)
        self.icd_list = self._load_icd_list()
        self.counts = self._load_counts()
        
    def _load_icd_list(self) -> List[Dict[str, str]]:
        """Load and parse ICD-10 code list."""
        icd_file = self.data_dir / 'icd_list.json'
        if not icd_file.exists():
            raise FileNotFoundError(f"ICD list not found at {icd_file}")
        
        with open(icd_file, 'r') as f:
            raw_list = json.load(f)
        
        parsed_list = []
        for entry in raw_list:
            if ':' in entry:
                desc, code = entry.split(':', 1)
                parsed_list.append({
                    'description': desc.strip().lower(),
                    'code': code.strip()
                })
        
        return parsed_list
    
    def _load_counts(self) -> Dict:
        """Load historical diagnosis counts."""
        counts_file = self.data_dir / 'counts.pickle'
        if not counts_file.exists():
            return {}
        
        with open(counts_file, 'rb') as f:
            return pickle.load(f)
    
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
        
        Args:
            patient: Patient details
            top_n: Number of top predictions to return
            
        Returns:
            List of ICD predictions sorted by probability score
        """
        all_symptoms = patient.symptoms + patient.primary_complaints
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
