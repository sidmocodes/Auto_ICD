"""Tests for MCP server module."""

import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_server'))

from auto_icd_mcp.server import AutoICDMCPServer
from auto_icd_mcp.predictor import PatientValidationError


class TestAutoICDMCPServer:
    """Tests for AutoICDMCPServer class."""
    
    @pytest.fixture
    def server(self):
        """Create server instance for tests."""
        return AutoICDMCPServer()
    
    def test_server_initialization(self, server):
        """Test that server initializes correctly."""
        assert server.server is not None
        assert server.predictor is not None
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_valid_input(self, server):
        """Test predict_icd_codes with valid input."""
        arguments = {
            'age': 30,
            'sex': 'M',
            'symptoms': ['headache', 'fatigue']
        }
        result = await server._predict_icd_codes(arguments)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert 'patient_summary' in data
        assert 'predictions' in data
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_missing_age(self, server):
        """Test predict_icd_codes with missing age."""
        arguments = {
            'sex': 'M',
            'symptoms': ['headache']
        }
        result = await server._predict_icd_codes(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
        assert 'Missing required fields' in data['message']
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_missing_symptoms(self, server):
        """Test predict_icd_codes with missing symptoms."""
        arguments = {
            'age': 30,
            'sex': 'M'
        }
        result = await server._predict_icd_codes(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_empty_symptoms(self, server):
        """Test predict_icd_codes with empty symptoms list."""
        arguments = {
            'age': 30,
            'sex': 'M',
            'symptoms': []
        }
        result = await server._predict_icd_codes(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
        assert 'At least one symptom' in data['message']
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_invalid_age(self, server):
        """Test predict_icd_codes with invalid age."""
        arguments = {
            'age': 'invalid',
            'sex': 'M',
            'symptoms': ['headache']
        }
        result = await server._predict_icd_codes(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_predict_icd_codes_negative_age(self, server):
        """Test predict_icd_codes with negative age."""
        arguments = {
            'age': -5,
            'sex': 'M',
            'symptoms': ['headache']
        }
        result = await server._predict_icd_codes(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_get_icd_info_valid_code(self, server):
        """Test get_icd_info with valid code."""
        arguments = {'code': 'G91.2'}
        result = await server._get_icd_info(arguments)
        
        data = json.loads(result[0].text)
        # Code may or may not be found depending on database
        assert 'icd_code' in data
    
    @pytest.mark.asyncio
    async def test_get_icd_info_missing_code(self, server):
        """Test get_icd_info with missing code."""
        arguments = {}
        result = await server._get_icd_info(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_get_icd_info_empty_code(self, server):
        """Test get_icd_info with empty code."""
        arguments = {'code': ''}
        result = await server._get_icd_info(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_search_icd_by_description_valid_query(self, server):
        """Test search_icd_by_description with valid query."""
        arguments = {'query': 'headache'}
        result = await server._search_icd_by_description(arguments)
        
        data = json.loads(result[0].text)
        assert 'results' in data
        assert 'total_found' in data
    
    @pytest.mark.asyncio
    async def test_search_icd_by_description_missing_query(self, server):
        """Test search_icd_by_description with missing query."""
        arguments = {}
        result = await server._search_icd_by_description(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
    
    @pytest.mark.asyncio
    async def test_search_icd_by_description_short_query(self, server):
        """Test search_icd_by_description with too short query."""
        arguments = {'query': 'a'}
        result = await server._search_icd_by_description(arguments)
        
        data = json.loads(result[0].text)
        assert 'error' in data
        assert 'at least 2 characters' in data['message']
    
    @pytest.mark.asyncio
    async def test_search_icd_by_description_with_limit(self, server):
        """Test search_icd_by_description with custom limit."""
        arguments = {'query': 'pain', 'limit': 5}
        result = await server._search_icd_by_description(arguments)
        
        data = json.loads(result[0].text)
        assert data['limit_applied'] == 5
        assert len(data['results']) <= 5
