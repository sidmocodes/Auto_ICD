"""Tests for predictor.py module."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_server'))

from auto_icd_mcp.predictor import (
    PatientDetails,
    PatientValidationError,
    PredictorDataError,
    EnhancedICDPredictor,
    ICDPrediction,
    validate_range,
    AGE_MIN, AGE_MAX,
    HEIGHT_MIN, HEIGHT_MAX,
    WEIGHT_MIN, WEIGHT_MAX
)


class TestValidateRange:
    """Tests for validate_range function."""
    
    def test_valid_value(self):
        """Test with value within range."""
        validate_range(50, 0, 100, "Test Field")  # Should not raise
    
    def test_value_at_minimum(self):
        """Test with value at minimum boundary."""
        validate_range(0, 0, 100, "Test Field")  # Should not raise
    
    def test_value_at_maximum(self):
        """Test with value at maximum boundary."""
        validate_range(100, 0, 100, "Test Field")  # Should not raise
    
    def test_none_value(self):
        """Test with None value (should be allowed)."""
        validate_range(None, 0, 100, "Test Field")  # Should not raise
    
    def test_value_below_minimum(self):
        """Test with value below minimum raises error."""
        with pytest.raises(PatientValidationError, match="must be between"):
            validate_range(-1, 0, 100, "Test Field")
    
    def test_value_above_maximum(self):
        """Test with value above maximum raises error."""
        with pytest.raises(PatientValidationError, match="must be between"):
            validate_range(101, 0, 100, "Test Field")
    
    def test_non_numeric_value(self):
        """Test with non-numeric value raises error."""
        with pytest.raises(PatientValidationError, match="must be a valid number"):
            validate_range("abc", 0, 100, "Test Field")


class TestPatientDetails:
    """Tests for PatientDetails dataclass."""
    
    def test_valid_patient_minimal(self):
        """Test creating patient with minimal required fields."""
        patient = PatientDetails(age=30, sex="M", symptoms=["headache"])
        assert patient.age == 30
        assert patient.sex == "M"
        assert patient.symptoms == ["headache"]
    
    def test_valid_patient_full(self):
        """Test creating patient with all fields."""
        patient = PatientDetails(
            age=45,
            sex="F",
            height_cm=165,
            weight_kg=70,
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            temperature_c=36.6,
            respiratory_rate=16,
            symptoms=["chest pain", "shortness of breath"],
            primary_complaints=["chest pain"],
            medical_history=["hypertension"],
            comorbidities=["diabetes"],
            doctor_specialty="CARDIOLOGY"
        )
        assert patient.age == 45
        assert patient.sex == "F"
        assert patient.bmi is not None
    
    def test_sex_normalization_male(self):
        """Test that 'male' is normalized to 'M'."""
        patient = PatientDetails(age=30, sex="male", symptoms=["cough"])
        assert patient.sex == "M"
    
    def test_sex_normalization_female(self):
        """Test that 'female' is normalized to 'F'."""
        patient = PatientDetails(age=30, sex="Female", symptoms=["cough"])
        assert patient.sex == "F"
    
    def test_invalid_sex_raises_error(self):
        """Test that invalid sex raises PatientValidationError."""
        with pytest.raises(PatientValidationError, match="Sex must be one of"):
            PatientDetails(age=30, sex="X", symptoms=["cough"])
    
    def test_empty_sex_raises_error(self):
        """Test that empty sex raises PatientValidationError."""
        with pytest.raises(PatientValidationError, match="Sex is required"):
            PatientDetails(age=30, sex="", symptoms=["cough"])
    
    def test_invalid_age_negative(self):
        """Test that negative age raises PatientValidationError."""
        with pytest.raises(PatientValidationError, match="Age must be between"):
            PatientDetails(age=-5, sex="M", symptoms=["cough"])
    
    def test_invalid_age_too_high(self):
        """Test that age over 150 raises PatientValidationError."""
        with pytest.raises(PatientValidationError, match="Age must be between"):
            PatientDetails(age=200, sex="M", symptoms=["cough"])
    
    def test_invalid_height_too_low(self):
        """Test that height below minimum raises error."""
        with pytest.raises(PatientValidationError, match="Height must be between"):
            PatientDetails(age=30, sex="M", symptoms=["cough"], height_cm=10)
    
    def test_invalid_weight_too_high(self):
        """Test that weight above maximum raises error."""
        with pytest.raises(PatientValidationError, match="Weight must be between"):
            PatientDetails(age=30, sex="M", symptoms=["cough"], weight_kg=1000)
    
    def test_invalid_bp_diastolic_higher_than_systolic(self):
        """Test that diastolic >= systolic raises error."""
        with pytest.raises(PatientValidationError, match="Diastolic BP"):
            PatientDetails(
                age=30, sex="M", symptoms=["cough"],
                systolic_bp=100, diastolic_bp=120
            )
    
    def test_bmi_calculation(self):
        """Test BMI calculation."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180, weight_kg=80
        )
        expected_bmi = round(80 / (1.8 ** 2), 2)
        assert patient.bmi == expected_bmi
    
    def test_bmi_none_without_height(self):
        """Test BMI is None when height is missing."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            weight_kg=80
        )
        assert patient.bmi is None
    
    def test_bmi_none_without_weight(self):
        """Test BMI is None when weight is missing."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180
        )
        assert patient.bmi is None
    
    def test_bmi_category_underweight(self):
        """Test BMI category for underweight."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180, weight_kg=50
        )
        assert patient.bmi_category == "Underweight"
    
    def test_bmi_category_normal(self):
        """Test BMI category for normal weight."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180, weight_kg=70
        )
        assert patient.bmi_category == "Normal"
    
    def test_bmi_category_overweight(self):
        """Test BMI category for overweight."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180, weight_kg=85
        )
        assert patient.bmi_category == "Overweight"
    
    def test_bmi_category_obese(self):
        """Test BMI category for obese."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            height_cm=180, weight_kg=110
        )
        assert patient.bmi_category == "Obese"
    
    def test_bp_category_normal(self):
        """Test BP category for normal blood pressure."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            systolic_bp=110, diastolic_bp=70
        )
        assert patient.bp_category == "Normal"
    
    def test_bp_category_elevated(self):
        """Test BP category for elevated blood pressure."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["cough"],
            systolic_bp=125, diastolic_bp=75
        )
        assert patient.bp_category == "Elevated"
    
    def test_symptoms_sanitization(self):
        """Test that symptoms are sanitized."""
        patient = PatientDetails(
            age=30, sex="M",
            symptoms=["  headache  ", "", "  ", "fever"]
        )
        assert patient.symptoms == ["headache", "fever"]
    
    def test_default_empty_lists(self):
        """Test that None lists default to empty lists."""
        patient = PatientDetails(age=30, sex="M", symptoms=None)
        assert patient.symptoms == []
        assert patient.primary_complaints == []
        assert patient.medical_history == []
        assert patient.comorbidities == []


class TestEnhancedICDPredictor:
    """Tests for EnhancedICDPredictor class."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance for tests."""
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return EnhancedICDPredictor(data_dir=data_dir)
    
    def test_predictor_initialization(self, predictor):
        """Test that predictor initializes correctly."""
        assert predictor.icd_list is not None
        assert len(predictor.icd_list) > 0
        assert isinstance(predictor.counts, dict)
    
    def test_predict_returns_list(self, predictor):
        """Test that predict returns a list."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["headache"]
        )
        predictions = predictor.predict(patient, top_n=5)
        assert isinstance(predictions, list)
    
    def test_predict_respects_top_n(self, predictor):
        """Test that predict respects top_n parameter."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["pain"]
        )
        predictions = predictor.predict(patient, top_n=5)
        assert len(predictions) <= 5
    
    def test_predict_returns_icd_predictions(self, predictor):
        """Test that predict returns ICDPrediction objects."""
        patient = PatientDetails(
            age=30, sex="M", symptoms=["headache"]
        )
        predictions = predictor.predict(patient, top_n=5)
        if len(predictions) > 0:
            assert isinstance(predictions[0], ICDPrediction)
    
    def test_predict_invalid_patient_raises_error(self, predictor):
        """Test that predict with invalid patient raises error."""
        with pytest.raises(PatientValidationError):
            predictor.predict("not a patient", top_n=5)
    
    def test_predict_invalid_top_n_raises_error(self, predictor):
        """Test that predict with invalid top_n raises error."""
        patient = PatientDetails(age=30, sex="M", symptoms=["headache"])
        with pytest.raises(ValueError):
            predictor.predict(patient, top_n=0)
    
    def test_predict_caps_top_n_at_100(self, predictor):
        """Test that top_n is capped at 100."""
        patient = PatientDetails(age=30, sex="M", symptoms=["pain"])
        predictions = predictor.predict(patient, top_n=200)
        assert len(predictions) <= 100


class TestICDPrediction:
    """Tests for ICDPrediction dataclass."""
    
    def test_to_dict(self):
        """Test ICDPrediction to_dict method."""
        pred = ICDPrediction(
            code="R07.9",
            description="Chest pain",
            probability_score=0.85,
            matched_symptoms=["chest pain"],
            related_vitals={"blood_pressure": "120/80"},
            confidence_level="High",
            matching_explanation="Matched symptoms"
        )
        result = pred.to_dict()
        
        assert result['icd_code'] == "R07.9"
        assert result['description'] == "Chest pain"
        assert result['probability_score'] == 0.85
        assert result['confidence_level'] == "High"
        assert result['matched_symptoms'] == ["chest pain"]
