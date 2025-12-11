#!/usr/bin/env python3
"""
Servidor HTTP simple para el frontend de SmartHealth
"""
import http.server
import socketserver
import os
import sys

# Cambiar al directorio del script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Agregar headers CORS para desarrollo
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Log personalizado
        sys.stderr.write("%s - - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format%args))

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Servidor HTTP ejecutándose en http://localhost:{PORT}")
        print(f"Directorio: {os.getcwd()}")
        print(f"Archivos disponibles:")
        print(f"  - http://localhost:{PORT}/public/index.html")
        print(f"  - http://localhost:{PORT}/public/test.html")
        print("\nPresiona Ctrl+C para detener el servidor\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServidor detenido.")
            sys.exit(0)

