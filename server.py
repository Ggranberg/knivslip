#!/usr/bin/env python3
"""Knivslip lokal server — servar hemsidan + sparar JSON-data via API."""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8080
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ALLOWED_FILES = ['users.json', 'timelog.json', 'customers.json', 'orders.json',
                 'knives.json', 'invoices.json', 'transactions.json', 'schedule.json',
                 'pricing.json', 'areas.json']

class KnivslipHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        # API: POST /api/save/filename.json
        if path.startswith('/api/save/'):
            filename = path.split('/api/save/')[-1]
            if filename not in ALLOWED_FILES:
                self.send_error(403, 'Fil ej tillaten')
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        # Disable caching for JSON files
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('', PORT), KnivslipHandler)
    print(f'Knivslip server koer pa http://localhost:{PORT}')
    print(f'Admin: http://localhost:{PORT}/website/admin.html')
    print(f'Hemsida: http://localhost:{PORT}/website/index.html')
    print('Tryck Ctrl+C for att stoppa')
    server.serve_forever()
