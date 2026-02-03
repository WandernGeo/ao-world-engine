#!/usr/bin/env python3
"""
RE:ECHO City Combined Frontend
Serves landing page, visualizer, and chat interface.
"""
import os
from flask import Flask, send_from_directory, render_template

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

@app.route('/')
def landing():
    """Landing page with navigation to Explore and Chat."""
    return render_template('landing.html')

@app.route('/explore')
def explore():
    """Visualizer - Map view with buildings and NPCs."""
    return send_from_directory('static', 'visualizer.html')

@app.route('/chat')
def chat():
    """Chat interface for talking to NPCs."""
    return send_from_directory('static', 'chat.html')

# Health check for Cloud Run
@app.route('/health')
def health():
    return {'status': 'ok'}, 200

# Static file handling
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# Legacy route support (old demo links)
@app.route('/index.html')
def legacy_index():
    return send_from_directory('static', 'chat.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True)
