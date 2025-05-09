from flask import Blueprint, jsonify, request
from app.utils import process_content, analyze_url
from app.logger import setup_logger
from app.status_store import set_status, get_status
import uuid
import threading

# Initialize logger
logger = setup_logger('routes')

main = Blueprint('main', __name__)

@main.route('/api/analyze', methods=['POST'])
def analyze_content():
    logger.info("Received request to /api/analyze")
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            logger.warning("No content provided in request")
            return jsonify({'error': 'No content provided'}), 400
            
        content = data['content']
        logger.debug(f"Processing content of length: {len(content)}")
        result = process_content(content)
        logger.info("Successfully processed content")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/analyze-url', methods=['POST'])
def analyze_url_endpoint():
    logger.info("Received request to /api/analyze-url")
    try:
        
        data = request.get_json()
        
        if not data or 'url' not in data:
            logger.warning("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
            
        url = data['url']
        max_pages = data.get('max_pages', 4)  # Default to 4 if not specified
        
        logger.debug(f"URL: {url}, max_pages: {max_pages}")
        # Validate max_pages
        try:
            max_pages = int(max_pages)
            if max_pages < 1:
                logger.warning(f"Invalid max_pages value: {max_pages}")
                return jsonify({'error': 'max_pages must be at least 1'}), 400
            if max_pages > 10:
                logger.warning(f"max_pages exceeds limit: {max_pages}")
                return jsonify({'error': 'max_pages cannot exceed 10'}), 400
        except ValueError:
            logger.warning(f"Invalid max_pages format: {max_pages}")
            return jsonify({'error': 'max_pages must be a valid integer'}), 400
        
        task_id = str(uuid.uuid4())
        set_status(task_id, {"step": "queued", "progress": 0, "message": "Task queued"})

        def background_task(url, max_pages, task_id):
            try:
                analyze_url(url, max_pages, task_id=task_id)
            except Exception as e:
                set_status(task_id, {"step": "error", "progress": 100, "message": str(e)})

        thread = threading.Thread(target=background_task, args=(url, max_pages, task_id))
        thread.start()

        return jsonify({"task_id": task_id}), 202
    except Exception as e:
        logger.error(f"Error analyzing URL: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/health', methods=['GET'])
def health_check():
    logger.debug("Health check request received")
    return jsonify({'status': 'healthy'})

@main.route('/api/analyze-status', methods=['GET'])
def analyze_status():
    task_id = request.args.get('task_id')
    status = get_status(task_id)
    if status is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(status) 