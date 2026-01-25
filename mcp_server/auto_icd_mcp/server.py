"""MCP Server for Auto ICD-10 Disease Prediction."""

import asyncio
import json
import sys
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

from .predictor import EnhancedICDPredictor, PatientDetails


class AutoICDMCPServer:
    """MCP Server for ICD-10 disease prediction."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("auto-icd-server")
        self.predictor = EnhancedICDPredictor()
        self._setup_handlers()
    
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
        try:
            # Normalize sex input
            sex = arguments['sex'][0].upper() if arguments['sex'] else 'M'
            
            # Create patient details
            patient = PatientDetails(
                age=arguments['age'],
                sex=sex,
                height_cm=arguments.get('height_cm'),
                weight_kg=arguments.get('weight_kg'),
                systolic_bp=arguments.get('systolic_bp'),
                diastolic_bp=arguments.get('diastolic_bp'),
                heart_rate=arguments.get('heart_rate'),
                temperature_c=arguments.get('temperature_c'),
                respiratory_rate=arguments.get('respiratory_rate'),
                symptoms=arguments.get('symptoms', []),
                primary_complaints=arguments.get('primary_complaints', []),
                medical_history=arguments.get('medical_history', []),
                comorbidities=arguments.get('comorbidities', []),
                doctor_specialty=arguments.get('doctor_specialty')
            )
            
            # Get predictions
            top_n = arguments.get('top_n', 10)
            predictions = self.predictor.predict(patient, top_n=top_n)
            
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
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "message": "Failed to predict ICD codes. Please check your input parameters."
                }, indent=2)
            )]
    
    async def _get_icd_info(self, arguments: dict) -> list[TextContent]:
        """Get information about a specific ICD code."""
        try:
            code = arguments['code'].strip()
            
            # Search for the code
            for icd_entry in self.predictor.icd_list:
                if icd_entry['code'] == code:
                    result = {
                        "icd_code": icd_entry['code'],
                        "description": icd_entry['description'].capitalize(),
                        "found": True
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
            
            # Code not found
            return [TextContent(
                type="text",
                text=json.dumps({
                    "icd_code": code,
                    "found": False,
                    "message": f"ICD-10 code '{code}' not found in database."
                }, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "message": "Failed to retrieve ICD code information."
                }, indent=2)
            )]
    
    async def _search_icd_by_description(self, arguments: dict) -> list[TextContent]:
        """Search ICD codes by description."""
        try:
            query = arguments['query'].lower().strip()
            limit = arguments.get('limit', 20)
            
            results = []
            for icd_entry in self.predictor.icd_list:
                if query in icd_entry['description']:
                    results.append({
                        "icd_code": icd_entry['code'],
                        "description": icd_entry['description'].capitalize()
                    })
                    
                    if len(results) >= limit:
                        break
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": arguments['query'],
                    "results": results,
                    "total_found": len(results)
                }, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "message": "Failed to search ICD codes."
                }, indent=2)
            )]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for the MCP server."""
    server = AutoICDMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
