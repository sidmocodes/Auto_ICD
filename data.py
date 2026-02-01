from flask import request
import pickle
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


def validate_input(age: str, sex: str, doctor: str, search_string: str) -> tuple:
    """
    Validate and sanitize input parameters.
    
    Args:
        age: Patient age as string
        sex: Patient sex
        doctor: Doctor specialty
        search_string: Search query string
        
    Returns:
        Tuple of validated (age, sex, doctor, search_string)
        
    Raises:
        ValidationError: If any input is invalid
    """
    # Validate age
    if not age or not age.strip():
        raise ValidationError("Age is required")
    
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 150:
            raise ValidationError("Age must be between 0 and 150")
    except ValueError:
        raise ValidationError("Age must be a valid number")
    
    # Validate sex
    if not sex or not sex.strip():
        raise ValidationError("Sex is required")
    
    sex = sex.strip().upper()
    if sex not in ['M', 'F', 'MALE', 'FEMALE']:
        raise ValidationError("Sex must be 'M', 'F', 'Male', or 'Female'")
    
    # Normalize sex to single character
    sex = 'M' if sex in ['M', 'MALE'] else 'F'
    
    # Validate doctor specialty
    if not doctor or not doctor.strip():
        doctor = 'GENERAL'  # Default value
    else:
        doctor = doctor.strip().upper()
    
    # Validate search string
    if not search_string or not search_string.strip():
        raise ValidationError("Search input is required")
    
    search_string = search_string.strip().lower()
    
    # Sanitize search string (remove potentially harmful characters)
    search_string = ''.join(c for c in search_string if c.isalnum() or c.isspace() or c in '-_.')
    
    return age, sex, doctor, search_string


def load_counts_data(filepath: str = 'counts.pickle') -> dict:
    """
    Load historical diagnosis counts from pickle file.
    
    Args:
        filepath: Path to the counts pickle file
        
    Returns:
        Dictionary of counts data
        
    Raises:
        DataLoadError: If file cannot be loaded
    """
    if not os.path.exists(filepath):
        logger.warning(f"Counts file not found at {filepath}, using empty counts")
        return {}
    
    try:
        with open(filepath, 'rb') as readFile:
            counts = pickle.load(readFile)
            logger.info(f"Successfully loaded counts data with {len(counts)} entries")
            return counts
    except (pickle.UnpicklingError, EOFError) as e:
        logger.error(f"Failed to unpickle counts file: {e}")
        raise DataLoadError(f"Counts file is corrupted: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading counts: {e}")
        raise DataLoadError(f"Failed to load counts data: {e}")


def load_icd_list(filepath: str = 'icd_list.json') -> list:
    """
    Load ICD code list from JSON file.
    
    Args:
        filepath: Path to the ICD list JSON file
        
    Returns:
        List of ICD codes
        
    Raises:
        DataLoadError: If file cannot be loaded
    """
    if not os.path.exists(filepath):
        logger.error(f"ICD list file not found at {filepath}")
        raise DataLoadError(f"ICD list file not found at {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            icd_list = json.load(f)
            logger.info(f"Successfully loaded ICD list with {len(icd_list)} entries")
            return icd_list
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ICD list JSON: {e}")
        raise DataLoadError(f"ICD list file contains invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading ICD list: {e}")
        raise DataLoadError(f"Failed to load ICD list: {e}")


def parse_icd_entry(entry: str) -> tuple:
    """
    Parse a single ICD entry string into description and code.
    
    Args:
        entry: ICD entry string in format "description : code"
        
    Returns:
        Tuple of (description, code) or (None, None) if invalid
    """
    if ':' not in entry:
        logger.warning(f"Invalid ICD entry format (missing colon): {entry[:50]}...")
        return None, None
    
    try:
        desc, code = entry.split(':', 1)
        desc = desc.strip().lower()
        code = code.strip()
        
        if not desc or not code:
            logger.warning(f"Empty description or code in entry: {entry[:50]}...")
            return None, None
        
        return desc, code
    except Exception as e:
        logger.warning(f"Failed to parse ICD entry: {e}")
        return None, None


def get_data():
    """
    Get ICD code suggestions based on patient information and search query.
    
    Returns:
        List of dictionaries containing ICD codes and descriptions
        
    Raises:
        ValidationError: If input validation fails
        DataLoadError: If data files cannot be loaded
    """
    data_to_send = []
    
    # Extract and validate form data
    try:
        age = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip()
        doctor = request.form.get("doctor", "GENERAL").strip()
        string = request.form.get('input', "").strip()
    except Exception as e:
        logger.error(f"Failed to extract form data: {e}")
        raise ValidationError(f"Failed to read form data: {e}")
    
    # Validate inputs
    age, sex, doctor, string = validate_input(age, sex, doctor, string)
    
    key = tuple([age, sex, doctor])
    logger.info(f"Processing request with key: {key}, search: '{string}'")
    
    # Load data files
    counts = load_counts_data()
    icd_list = load_icd_list()

    if key in counts.keys():
        counts_codes = []
        counts_count = []
        
        try:
            for item in counts[key]:
                if len(item) >= 2:
                    counts_codes.append(item[0])
                    counts_count.append(item[1])
        except (TypeError, IndexError) as e:
            logger.warning(f"Error processing counts data for key {key}: {e}")
            counts_codes = []
            counts_count = []

        logger.debug(f"Key is present, mined codes: {counts_codes}")
        
        desc_list = []
        code_list = []
        
        for desc_code in icd_list:
            desc, code = parse_icd_entry(desc_code)
            if desc is None or code is None:
                continue

            if string in desc:
                desc_list.append(desc)
                code_list.append(code)

        intersection = set(code_list).intersection(set(counts_codes))
        
        if len(intersection) == 0:
            for desc, code in zip(desc_list, code_list):
                data_to_send.append({"desc": desc, "code": code})
        else:
            for intersecting_code in intersection:
                try:
                    counts_code_idx = counts_codes.index(intersecting_code)
                    code = counts_codes[counts_code_idx]
                    desc_idx = code_list.index(intersecting_code)
                    desc = desc_list[desc_idx]
                    freq_score = counts_count[counts_code_idx]

                    logger.debug(f"Found intersection - code: {code}, desc: {desc}, score: {freq_score}")

                    data_to_send.append({"desc": desc, "code": code, "score": freq_score})
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error processing intersecting code {intersecting_code}: {e}")
                    continue

        logger.debug(f"Found {len(desc_list)} descriptions, {len(intersection)} intersections")

    else:
        logger.debug("Key is not present in counts, performing direct search")
        
        for desc_code in icd_list:
            desc, code = parse_icd_entry(desc_code)
            if desc is None or code is None:
                continue

            if string in desc:
                data_to_send.append({"desc": desc, "code": code})

    # Sort by score if available
    if len(data_to_send) > 0 and "score" in data_to_send[0].keys():
        try:
            data_to_send = sorted(data_to_send, key=lambda x: x.get("score", 0), reverse=True)
        except (TypeError, KeyError) as e:
            logger.warning(f"Error sorting results: {e}")

    logger.info(f"Returning {len(data_to_send)} results")
    return data_to_send
