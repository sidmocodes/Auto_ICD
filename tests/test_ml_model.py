"""Tests for the ML model module."""

import pytest
import os
from pathlib import Path


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestICDMLModel:
    """Tests for the ICDMLModel class."""
    
    def test_import_ml_model(self):
        """Test that ML model can be imported."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel, MLModelError
        assert ICDMLModel is not None
        assert MLModelError is not None
    
    def test_model_initialization(self):
        """Test that ML model initializes correctly."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        
        model = ICDMLModel(data_dir=str(PROJECT_ROOT))
        assert model is not None
        assert len(model.icd_data) > 0
        assert len(model.descriptions) > 0
        assert len(model.codes) > 0
        assert model.vectorizer is not None
        assert model.tfidf_matrix is not None
    
    def test_model_loads_icd_codes(self):
        """Test that model loads ICD codes correctly."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        
        model = ICDMLModel(data_dir=str(PROJECT_ROOT))
        # Should load a large number of ICD codes
        assert len(model.icd_data) > 40000
    
    def test_model_loads_historical_counts(self):
        """Test that model loads historical counts if available."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        
        model = ICDMLModel(data_dir=str(PROJECT_ROOT))
        # Historical counts should be loaded
        assert isinstance(model.historical_counts, dict)
    
    def test_tfidf_matrix_shape(self):
        """Test TF-IDF matrix has correct shape."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        
        model = ICDMLModel(data_dir=str(PROJECT_ROOT))
        # Matrix should have rows = number of ICD codes
        assert model.tfidf_matrix.shape[0] == len(model.icd_data)


class TestMLModelPredictions:
    """Tests for ML model predictions."""
    
    @pytest.fixture
    def model(self):
        """Create ML model fixture."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        return ICDMLModel(data_dir=str(PROJECT_ROOT))
    
    def test_predict_returns_list(self, model):
        """Test predict returns a list."""
        predictions = model.predict(symptoms=['headache', 'fever'])
        assert isinstance(predictions, list)
    
    def test_predict_returns_correct_structure(self, model):
        """Test predictions have correct structure."""
        predictions = model.predict(symptoms=['chest pain'], top_n=5)
        
        assert len(predictions) <= 5
        for pred in predictions:
            assert 'code' in pred
            assert 'description' in pred
            assert 'probability_score' in pred
            assert 'confidence_level' in pred
            assert 'matched_symptoms' in pred
            assert 'scores' in pred
    
    def test_predict_empty_symptoms_returns_empty(self, model):
        """Test predict with empty symptoms returns empty list."""
        predictions = model.predict(symptoms=[])
        assert predictions == []
    
    def test_predict_respects_top_n(self, model):
        """Test predict respects top_n parameter."""
        predictions = model.predict(symptoms=['pain', 'fever'], top_n=3)
        assert len(predictions) <= 3
    
    def test_predict_with_age_and_sex(self, model):
        """Test predict works with age and sex."""
        predictions = model.predict(
            symptoms=['cough', 'fever'],
            age=45,
            sex='M',
            top_n=5
        )
        assert isinstance(predictions, list)
        assert len(predictions) > 0
    
    def test_predict_with_specialty(self, model):
        """Test predict works with specialty."""
        predictions = model.predict(
            symptoms=['chest pain'],
            age=55,
            sex='F',
            specialty='CARDIOLOGY',
            top_n=5
        )
        assert isinstance(predictions, list)
    
    def test_predict_with_vitals(self, model):
        """Test predict works with vitals."""
        predictions = model.predict(
            symptoms=['hypertension'],
            vitals={
                'bmi': 28.5,
                'systolic_bp': 150,
                'diastolic_bp': 95
            },
            top_n=5
        )
        assert isinstance(predictions, list)
    
    def test_predict_scores_are_normalized(self, model):
        """Test probability scores are between 0 and 1."""
        predictions = model.predict(symptoms=['diabetes'], top_n=10)
        
        for pred in predictions:
            assert 0 <= pred['probability_score'] <= 1
    
    def test_predict_confidence_levels_valid(self, model):
        """Test confidence levels are valid values."""
        predictions = model.predict(symptoms=['headache'], top_n=10)
        valid_levels = ['High', 'Medium', 'Low']
        
        for pred in predictions:
            assert pred['confidence_level'] in valid_levels


class TestMLModelScoring:
    """Tests for ML model scoring components."""
    
    @pytest.fixture
    def model(self):
        """Create ML model fixture."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        return ICDMLModel(data_dir=str(PROJECT_ROOT))
    
    def test_scores_breakdown_present(self, model):
        """Test that score breakdown is present."""
        predictions = model.predict(symptoms=['fever'], top_n=1)
        
        if predictions:
            scores = predictions[0]['scores']
            assert 'tfidf_similarity' in scores
            assert 'historical_probability' in scores
            assert 'vitals_relevance' in scores
    
    def test_tfidf_score_positive_for_matching_symptoms(self, model):
        """Test TF-IDF score is positive for matching symptoms."""
        predictions = model.predict(symptoms=['headache'], top_n=5)
        
        # At least one prediction should have positive TF-IDF score
        tfidf_scores = [p['scores']['tfidf_similarity'] for p in predictions]
        assert max(tfidf_scores) > 0


class TestAgeBrackets:
    """Tests for age bracket conversion."""
    
    @pytest.fixture
    def model(self):
        """Create ML model fixture."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        return ICDMLModel(data_dir=str(PROJECT_ROOT))
    
    def test_age_bracket_child(self, model):
        """Test age bracket for child."""
        bracket = model._get_age_bracket(5)
        assert bracket == '0-10'
    
    def test_age_bracket_teen(self, model):
        """Test age bracket for teenager."""
        bracket = model._get_age_bracket(15)
        assert bracket == '10-20'
    
    def test_age_bracket_adult(self, model):
        """Test age bracket for adult."""
        bracket = model._get_age_bracket(35)
        assert bracket == '30-40'
    
    def test_age_bracket_senior(self, model):
        """Test age bracket for senior."""
        bracket = model._get_age_bracket(75)
        assert bracket == '70-80'
    
    def test_age_bracket_elderly(self, model):
        """Test age bracket for elderly."""
        bracket = model._get_age_bracket(95)
        assert bracket == '90+'


class TestSexConversion:
    """Tests for sex string conversion."""
    
    @pytest.fixture
    def model(self):
        """Create ML model fixture."""
        from mcp_server.auto_icd_mcp.ml_model import ICDMLModel
        return ICDMLModel(data_dir=str(PROJECT_ROOT))
    
    def test_sex_male_uppercase(self, model):
        """Test sex conversion for male."""
        result = model._get_sex_string('M')
        assert result == 'MALE'
    
    def test_sex_male_full(self, model):
        """Test sex conversion for MALE."""
        result = model._get_sex_string('MALE')
        assert result == 'MALE'
    
    def test_sex_female_uppercase(self, model):
        """Test sex conversion for female."""
        result = model._get_sex_string('F')
        assert result == 'FEMALE'
    
    def test_sex_female_full(self, model):
        """Test sex conversion for FEMALE."""
        result = model._get_sex_string('FEMALE')
        assert result == 'FEMALE'


class TestIntegrationWithPredictor:
    """Integration tests for ML model with predictor."""
    
    def test_predictor_uses_ml_model_when_enabled(self):
        """Test that predictor uses ML model when enabled."""
        from mcp_server.auto_icd_mcp.predictor import EnhancedICDPredictor, PatientDetails
        
        predictor = EnhancedICDPredictor(data_dir=str(PROJECT_ROOT), use_ml=True)
        assert predictor.use_ml == True
        assert predictor.ml_model is not None
    
    def test_predictor_can_disable_ml_model(self):
        """Test that predictor can disable ML model."""
        from mcp_server.auto_icd_mcp.predictor import EnhancedICDPredictor
        
        predictor = EnhancedICDPredictor(data_dir=str(PROJECT_ROOT), use_ml=False)
        assert predictor.use_ml == False
        assert predictor.ml_model is None
    
    def test_ml_predictions_include_score_breakdown(self):
        """Test ML predictions include score breakdown in explanation."""
        from mcp_server.auto_icd_mcp.predictor import EnhancedICDPredictor, PatientDetails
        
        predictor = EnhancedICDPredictor(data_dir=str(PROJECT_ROOT), use_ml=True)
        patient = PatientDetails(
            age=45,
            sex='M',
            symptoms=['chest pain', 'shortness of breath']
        )
        
        predictions = predictor.predict(patient, top_n=3)
        assert len(predictions) > 0
        
        # Check that ML scores are in the explanation
        for pred in predictions:
            assert '[ML Score:' in pred.matching_explanation
    
    def test_ml_and_rule_based_both_return_predictions(self):
        """Test both ML and rule-based predictors return predictions."""
        from mcp_server.auto_icd_mcp.predictor import EnhancedICDPredictor, PatientDetails
        
        patient = PatientDetails(
            age=30,
            sex='F',
            symptoms=['headache', 'nausea']
        )
        
        # ML predictions
        ml_predictor = EnhancedICDPredictor(data_dir=str(PROJECT_ROOT), use_ml=True)
        ml_predictions = ml_predictor.predict(patient, top_n=5)
        
        # Rule-based predictions
        rule_predictor = EnhancedICDPredictor(data_dir=str(PROJECT_ROOT), use_ml=False)
        rule_predictions = rule_predictor.predict(patient, top_n=5)
        
        assert len(ml_predictions) > 0
        assert len(rule_predictions) > 0
