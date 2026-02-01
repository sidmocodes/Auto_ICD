"""MCP Server for Auto ICD-10 Disease Prediction."""

import asyncio
import json
import sys
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from .predictor import EnhancedICDPredictor, PatientDetails, PatientValidationError, PredictorDataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoICDMCPServer:
    """MCP Server for ICD-10 disease prediction."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("auto-icd-server")
        self.predictor = None
        self._init_predictor()
        self._setup_handlers()
    
    def _init_predictor(self):
        """Initialize the predictor with error handling."""
        try:
            self.predictor = EnhancedICDPredictor()
            logger.info("EnhancedICDPredictor initialized successfully")
        except PredictorDataError as e:
            logger.error(f"Failed to initialize predictor: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing predictor: {e}")
            raise
    
    def _setup_handlers(self):
        """Set up MCP server request handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="predict_icd_codes",
                    description="""Predict ICD-10 disease codes based on comprehensive patient details.
                    
This tool analyzes patient information including demographics, vitals, symptoms, and medical history 
to predict possible diseases with their ICD-10 codes, probability scores, and detailed explanations.

Returns top matching diseases with:
- ICD-10 code and description
- Probability score (0-1)
- Confidence level (High/Medium/Low)
- Matched symptoms from patient input
- Relevant vital signs analysis
- Detailed explanation of how patient details match the condition""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "age": {
                                "type": "integer",
                                "description": "Patient age in years",
                                "minimum": 0,
                                "maximum": 150
                            },
                            "sex": {
                                "type": "string",
                                "description": "Patient biological sex",
                                "enum": ["M", "F", "Male", "Female", "male", "female", "m", "f"]
                            },
                            "height_cm": {
                                "type": "number",
                                "description": "Patient height in centimeters (optional)",
                                "minimum": 0
                            },
                            "weight_kg": {
                                "type": "number",
                                "description": "Patient weight in kilograms (optional)",
                                "minimum": 0
                            },
                            "systolic_bp": {
                                "type": "integer",
                                "description": "Systolic blood pressure in mmHg (optional)",
                                "minimum": 0
                            },
                            "diastolic_bp": {
                                "type": "integer",
                                "description": "Diastolic blood pressure in mmHg (optional)",
                                "minimum": 0
                            },
                            "heart_rate": {
                                "type": "integer",
                                "description": "Heart rate in beats per minute (optional)",
                                "minimum": 0
                            },
                            "temperature_c": {
                                "type": "number",
                                "description": "Body temperature in Celsius (optional)",
                                "minimum": 0
                            },
                            "respiratory_rate": {
                                "type": "integer",
                                "description": "Respiratory rate in breaths per minute (optional)",
                                "minimum": 0
                            },
                            "symptoms": {
                                "type": "array",
                                "description": "List of symptoms the patient is experiencing",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "primary_complaints": {
                                "type": "array",
                                "description": "Primary complaints or chief concerns (optional)",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "medical_history": {
                                "type": "array",
                                "description": "Past medical conditions or surgeries (optional)",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "comorbidities": {
                                "type": "array",
                                "description": "Existing chronic conditions (optional)",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "doctor_specialty": {
                                "type": "string",
                                "description": "Medical specialty of attending physician (optional, e.g., 'CARDIOLOGY', 'GENERAL', 'NEUROLOGY')"
                            },
                            "top_n": {
                                "type": "integer",
                                "description": "Number of top predictions to return (default: 10)",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10
                            }
                        },
                        "required": ["age", "sex", "symptoms"]
                    }
                ),
                Tool(
                    name="get_icd_info",
                    description="""Get detailed information about a specific ICD-10 code.
                    
This tool looks up a specific ICD-10 code and returns its full description and related information.""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The ICD-10 code to look up (e.g., 'G91.2', 'Z3A.10')"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="search_icd_by_description",
                    description="""Search for ICD-10 codes by disease description or symptoms.
                    
This tool searches the ICD-10 database for codes matching a text query in their descriptions.""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (disease name, symptom, or description)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 20)",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            
            if name == "predict_icd_codes":
                return await self._predict_icd_codes(arguments)
            elif name == "get_icd_info":
                return await self._get_icd_info(arguments)
            elif name == "search_icd_by_description":
                return await self._search_icd_by_description(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _predict_icd_codes(self, arguments: dict) -> list[TextContent]:
        """Predict ICD codes based on patient details."""
        logger.info(f"Received prediction request with arguments: {list(arguments.keys())}")
        
        # Validate required fields
        required_fields = ['age', 'sex', 'symptoms']
        missing_fields = [f for f in required_fields if f not in arguments or arguments[f] is None]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.warning(error_msg)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": error_msg,
                    "required_fields": required_fields
                }, indent=2)
            )]
        
        # Validate age
        try:
            age = int(arguments['age'])
            if age < 0 or age > 150:
                raise ValueError("Age must be between 0 and 150")
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid age value: {arguments.get('age')}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": f"Invalid age: {e}"
                }, indent=2)
            )]
        
        # Validate symptoms
        symptoms = arguments.get('symptoms', [])
        if not isinstance(symptoms, list):
            logger.warning(f"Symptoms is not a list: {type(symptoms)}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": "Symptoms must be a list of strings"
                }, indent=2)
            )]
        
        if len(symptoms) == 0:
            logger.warning("Empty symptoms list provided")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": "At least one symptom is required"
                }, indent=2)
            )]
        
        try:
            # Normalize sex input
            sex_input = arguments.get('sex', '')
            if not sex_input:
                raise PatientValidationError("Sex is required")
            sex = sex_input[0].upper() if sex_input else 'M'
            
            # Create patient details
            patient = PatientDetails(
                age=age,
                sex=sex,
                height_cm=arguments.get('height_cm'),
                weight_kg=arguments.get('weight_kg'),
                systolic_bp=arguments.get('systolic_bp'),
                diastolic_bp=arguments.get('diastolic_bp'),
                heart_rate=arguments.get('heart_rate'),
                temperature_c=arguments.get('temperature_c'),
                respiratory_rate=arguments.get('respiratory_rate'),
                symptoms=symptoms,
                primary_complaints=arguments.get('primary_complaints', []),
                medical_history=arguments.get('medical_history', []),
                comorbidities=arguments.get('comorbidities', []),
                doctor_specialty=arguments.get('doctor_specialty')
            )
            
            # Get predictions
            top_n = arguments.get('top_n', 10)
            if not isinstance(top_n, int) or top_n < 1:
                top_n = 10
            top_n = min(top_n, 50)  # Cap at 50
            
            predictions = self.predictor.predict(patient, top_n=top_n)
            
            logger.info(f"Generated {len(predictions)} predictions for patient")
            
            # Format results
            result = {
                "patient_summary": {
                    "age": patient.age,
                    "sex": patient.sex,
                    "bmi": patient.bmi,
                    "bmi_category": patient.bmi_category,
                    "blood_pressure_category": patient.bp_category,
                    "symptoms_count": len(patient.symptoms),
                    "comorbidities_count": len(patient.comorbidities)
                },
                "predictions": [pred.to_dict() for pred in predictions],
                "total_predictions": len(predictions)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        except PatientValidationError as e:
            logger.warning(f"Patient validation error: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": str(e)
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Unexpected error in predict_icd_codes: {type(e).__name__}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Internal Error",
                    "error_type": type(e).__name__,
                    "message": "Failed to predict ICD codes. Please check your input parameters.",
                    "details": str(e)
                }, indent=2)
            )]
    
    async def _get_icd_info(self, arguments: dict) -> list[TextContent]:
        """Get information about a specific ICD code."""
        # Validate required field
        if 'code' not in arguments or not arguments['code']:
            logger.warning("ICD info request without code")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": "ICD code is required"
                }, indent=2)
            )]
        
        try:
            code = str(arguments['code']).strip().upper()
            logger.info(f"Looking up ICD code: {code}")
            
            if not code:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Validation Error",
                        "message": "ICD code cannot be empty"
                    }, indent=2)
                )]
            
            # Search for the code (case-insensitive)
            for icd_entry in self.predictor.icd_list:
                if icd_entry['code'].upper() == code:
                    result = {
                        "icd_code": icd_entry['code'],
                        "description": icd_entry['description'].capitalize(),
                        "found": True
                    }
                    logger.info(f"Found ICD code: {code}")
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
            
            # Code not found
            logger.info(f"ICD code not found: {code}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "icd_code": code,
                    "found": False,
                    "message": f"ICD-10 code '{code}' not found in database."
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error retrieving ICD info: {type(e).__name__}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Internal Error",
                    "message": "Failed to retrieve ICD code information.",
                    "details": str(e)
                }, indent=2)
            )]
    
    async def _search_icd_by_description(self, arguments: dict) -> list[TextContent]:
        """Search ICD codes by description."""
        # Validate required field
        if 'query' not in arguments or not arguments['query']:
            logger.warning("ICD search request without query")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation Error",
                    "message": "Search query is required"
                }, indent=2)
            )]
        
        try:
            query = str(arguments['query']).lower().strip()
            
            if not query:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Validation Error",
                        "message": "Search query cannot be empty"
                    }, indent=2)
                )]
            
            if len(query) < 2:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Validation Error",
                        "message": "Search query must be at least 2 characters long"
                    }, indent=2)
                )]
            
            limit = arguments.get('limit', 20)
            if not isinstance(limit, int) or limit < 1:
                limit = 20
            limit = min(limit, 100)  # Cap at 100
            
            logger.info(f"Searching ICD codes for query: '{query}' (limit: {limit})")
            
            results = []
            for icd_entry in self.predictor.icd_list:
                if query in icd_entry['description']:
                    results.append({
                        "icd_code": icd_entry['code'],
                        "description": icd_entry['description'].capitalize()
                    })
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} results for query: '{query}'")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": arguments['query'],
                    "results": results,
                    "total_found": len(results),
                    "limit_applied": limit
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error searching ICD codes: {type(e).__name__}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Internal Error",
                    "message": "Failed to search ICD codes.",
                    "details": str(e)
                }, indent=2)
            )]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Auto ICD MCP Server...")
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"Server error: {type(e).__name__}: {e}")
            raise


def main():
    """Main entry point for the MCP server."""
    logger.info("Initializing Auto ICD MCP Server")
    try:
        server = AutoICDMCPServer()
        asyncio.run(server.run())
    except PredictorDataError as e:
        logger.critical(f"Failed to start server due to data error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.critical(f"Unexpected error: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
