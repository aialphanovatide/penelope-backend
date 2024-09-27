from flask import Flask, request, jsonify, Blueprint
from app.penelope.image_generator_module.image import image_generator

image_bp = Blueprint('image_bp', __name__)

@image_bp.route('/generate-image', methods=['POST'])
def generate_image():
    """
    Endpoint to generate images based on a prompt.
    Expects a JSON body with 'prompt', 'number_images', and 'style' keys.
    """
    data = request.get_json()
    prompt = data.get('prompt')
    number_images = data.get('number_images', 1)
    style = data.get('style', 'vivid')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    if not (1 <= number_images <= 4):
        return jsonify({'error': 'Number of Images must be between 1 and 4'}), 400
    
    if style not in ['vivid', 'natural']:
        return jsonify({'error': 'Style must be either "vivid" or "natural"'}), 400

    try:
        image_urls = image_generator.generate_image(prompt=prompt, n=int(number_images), style=style)
        return jsonify({'image_urls': image_urls}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500