#!/usr/bin/env python3
"""
RE:ECHO City Demo - Static File Server
Serves the demo HTML and proxies to the NPC Chat API.
"""
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True)
