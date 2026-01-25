"""Setup script for Auto ICD MCP Server."""

from setuptools import setup, find_packages

setup(
    name="auto-icd-mcp-server",
    version="1.0.0",
    description="MCP server for ICD-10 disease code prediction based on patient details",
    author="Siddharth Mohanty",
    author_email="siddharthmohantywk@gmail.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.1.2",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "auto-icd-mcp=auto_icd_mcp.server:main",
        ],
    },
    license="MIT",
    keywords=["mcp", "icd-10", "medical", "diagnosis", "disease-prediction"],
)
