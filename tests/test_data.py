"""Tests for data.py module."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import (
    ValidationError,
    DataLoadError,
    validate_input,
    load_counts_data,
    load_icd_list,
    parse_icd_entry
)


class TestValidateInput:
    """Tests for validate_input function."""
    
    def test_valid_input(self):
        """Test with valid input values."""
        age, sex, doctor, search = validate_input("30", "M", "CARDIOLOGY", "chest pain")
        assert age == "30"
        assert sex == "M"
        assert doctor == "CARDIOLOGY"
        assert search == "chest pain"
    
    def test_valid_input_female(self):
        """Test with female sex value."""
        age, sex, doctor, search = validate_input("25", "female", "GENERAL", "headache")
        assert sex == "F"
    
    def test_valid_input_male_full(self):
        """Test with 'male' as sex value."""
        age, sex, doctor, search = validate_input("45", "Male", "NEUROLOGY", "fatigue")
        assert sex == "M"
    
    def test_default_doctor_specialty(self):
        """Test that empty doctor defaults to GENERAL."""
        age, sex, doctor, search = validate_input("30", "M", "", "pain")
        assert doctor == "GENERAL"
    
    def test_empty_age_raises_error(self):
        """Test that empty age raises ValidationError."""
        with pytest.raises(ValidationError, match="Age is required"):
            validate_input("", "M", "GENERAL", "pain")
    
    def test_invalid_age_raises_error(self):
        """Test that non-numeric age raises ValidationError."""
        with pytest.raises(ValidationError, match="Age must be a valid number"):
            validate_input("abc", "M", "GENERAL", "pain")
    
    def test_negative_age_raises_error(self):
        """Test that negative age raises ValidationError."""
        with pytest.raises(ValidationError, match="Age must be between 0 and 150"):
            validate_input("-5", "M", "GENERAL", "pain")
    
    def test_age_over_150_raises_error(self):
        """Test that age over 150 raises ValidationError."""
        with pytest.raises(ValidationError, match="Age must be between 0 and 150"):
            validate_input("200", "M", "GENERAL", "pain")
    
    def test_empty_sex_raises_error(self):
        """Test that empty sex raises ValidationError."""
        with pytest.raises(ValidationError, match="Sex is required"):
            validate_input("30", "", "GENERAL", "pain")
    
    def test_invalid_sex_raises_error(self):
        """Test that invalid sex raises ValidationError."""
        with pytest.raises(ValidationError, match="Sex must be"):
            validate_input("30", "X", "GENERAL", "pain")
    
    def test_empty_search_raises_error(self):
        """Test that empty search string raises ValidationError."""
        with pytest.raises(ValidationError, match="Search input is required"):
            validate_input("30", "M", "GENERAL", "")
    
    def test_whitespace_only_search_raises_error(self):
        """Test that whitespace-only search raises ValidationError."""
        with pytest.raises(ValidationError, match="Search input is required"):
            validate_input("30", "M", "GENERAL", "   ")


class TestParseIcdEntry:
    """Tests for parse_icd_entry function."""
    
    def test_valid_entry(self):
        """Test parsing a valid ICD entry."""
        desc, code = parse_icd_entry("Chest pain : R07.9")
        assert desc == "chest pain"
        assert code == "R07.9"
    
    def test_entry_with_extra_colons(self):
        """Test parsing entry with multiple colons."""
        desc, code = parse_icd_entry("Pain: chest area : R07.9")
        assert desc == "pain"
        assert code == "chest area : R07.9"
    
    def test_entry_without_colon(self):
        """Test parsing entry without colon returns None."""
        desc, code = parse_icd_entry("Invalid entry without colon")
        assert desc is None
        assert code is None
    
    def test_empty_description(self):
        """Test parsing entry with empty description."""
        desc, code = parse_icd_entry(" : R07.9")
        assert desc is None
        assert code is None
    
    def test_empty_code(self):
        """Test parsing entry with empty code."""
        desc, code = parse_icd_entry("Chest pain : ")
        assert desc is None
        assert code is None


class TestLoadIcdList:
    """Tests for load_icd_list function."""
    
    def test_load_existing_file(self):
        """Test loading the actual ICD list file."""
        icd_list = load_icd_list('icd_list.json')
        assert isinstance(icd_list, list)
        assert len(icd_list) > 0
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(DataLoadError, match="not found"):
            load_icd_list('nonexistent_file.json')


class TestLoadCountsData:
    """Tests for load_counts_data function."""
    
    def test_load_existing_file(self):
        """Test loading the actual counts file."""
        counts = load_counts_data('counts.pickle')
        assert isinstance(counts, dict)
    
    def test_load_nonexistent_file_returns_empty(self):
        """Test loading a non-existent file returns empty dict."""
        counts = load_counts_data('nonexistent_file.pickle')
        assert counts == {}
