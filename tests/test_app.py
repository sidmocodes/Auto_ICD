"""Tests for app.py Flask application."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'auto-icd-api'


class TestIndexEndpoint:
    """Tests for index endpoint."""
    
    def test_index_returns_200(self, client):
        """Test index page returns 200."""
        response = client.get('/')
        assert response.status_code == 200


class TestApiDocEndpoint:
    """Tests for API documentation endpoint."""
    
    def test_api_doc_returns_200(self, client):
        """Test API doc page returns 200."""
        response = client.get('/api-doc')
        assert response.status_code == 200


class TestSearchEndpoint:
    """Tests for search endpoint."""
    
    def test_search_get_returns_200(self, client):
        """Test search GET returns 200."""
        response = client.get('/search')
        assert response.status_code == 200
    
    def test_search_post_missing_fields(self, client):
        """Test search POST with missing fields."""
        response = client.post('/search', data={})
        # Should return page with error, not crash
        assert response.status_code == 200


class TestIcdEndpoint:
    """Tests for ICD endpoint."""
    
    def test_icd_get_returns_200(self, client):
        """Test ICD GET returns 200."""
        response = client.get('/icd')
        assert response.status_code == 200
    
    def test_icd_post_missing_fields(self, client):
        """Test ICD POST with missing fields returns error."""
        response = client.post('/icd', data={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_icd_post_valid_data(self, client):
        """Test ICD POST with valid data."""
        response = client.post('/icd', data={
            'age': '30',
            'sex': 'M',
            'doctor': 'GENERAL',
            'input': 'headache'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'count' in data
    
    def test_icd_post_invalid_age(self, client):
        """Test ICD POST with invalid age."""
        response = client.post('/icd', data={
            'age': 'invalid',
            'sex': 'M',
            'doctor': 'GENERAL',
            'input': 'headache'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestErrorHandlers:
    """Tests for error handlers."""
    
    def test_404_error(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Not Found'
