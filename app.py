from flask import Flask, render_template, request, jsonify
import logging

from data import get_data, ValidationError, DataLoadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# Custom error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle validation errors with a 400 Bad Request response."""
    logger.warning(f"Validation error: {error}")
    return jsonify({
        "error": "Validation Error",
        "message": str(error),
        "status": 400
    }), 400


@app.errorhandler(DataLoadError)
def handle_data_load_error(error):
    """Handle data loading errors with a 500 Internal Server Error response."""
    logger.error(f"Data load error: {error}")
    return jsonify({
        "error": "Data Load Error",
        "message": "Failed to load required data files. Please contact support.",
        "status": 500
    }), 500


@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found.",
        "status": 404
    }), 404


@app.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later.",
        "status": 500
    }), 500


@app.route("/")
def index():
    """Render the main autocomplete page."""
    try:
        return render_template('icd_autocomplete.html')
    except Exception as e:
        logger.error(f"Failed to render index page: {e}")
        return jsonify({"error": "Failed to load page"}), 500


@app.route("/search", methods=['GET', 'POST'])
def search():
    """Handle ICD code search requests."""
    if request.method == 'POST':
        try:
            data_to_send = get_data()
            return render_template('icd_search.html', posts=data_to_send)
        except ValidationError as e:
            logger.warning(f"Search validation error: {e}")
            return render_template('icd_search.html', posts=[], error=str(e))
        except DataLoadError as e:
            logger.error(f"Search data load error: {e}")
            return render_template('icd_search.html', posts=[], error="Failed to load data")
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return render_template('icd_search.html', posts=[], error="An unexpected error occurred")

    return render_template('icd_search.html')


@app.route('/icd', methods=['GET', 'POST'])
def icd():
    """API endpoint for ICD code predictions."""
    if request.method == 'POST':
        try:
            data_to_send = get_data()
            return jsonify({
                "success": True,
                "data": data_to_send,
                "count": len(data_to_send)
            })
        except ValidationError as e:
            logger.warning(f"ICD API validation error: {e}")
            return jsonify({
                "success": False,
                "error": "Validation Error",
                "message": str(e)
            }), 400
        except DataLoadError as e:
            logger.error(f"ICD API data load error: {e}")
            return jsonify({
                "success": False,
                "error": "Data Load Error",
                "message": "Failed to load required data"
            }), 500
        except Exception as e:
            logger.error(f"Unexpected error in ICD API: {e}")
            return jsonify({
                "success": False,
                "error": "Internal Error",
                "message": "An unexpected error occurred"
            }), 500

    try:
        return render_template('icd.html')
    except Exception as e:
        logger.error(f"Failed to render ICD page: {e}")
        return jsonify({"error": "Failed to load page"}), 500


@app.route('/api-doc')
def documentation():
    """Render the API documentation page."""
    try:
        return render_template('api_doc.html')
    except Exception as e:
        logger.error(f"Failed to render API documentation: {e}")
        return jsonify({"error": "Failed to load documentation"}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "auto-icd-api"
    }), 200


if __name__ == "__main__":
    logger.info("Starting Auto ICD Flask application")
    app.run(debug=True)
