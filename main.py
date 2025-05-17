print("\nRemember The Resolution Its Using Is Always The Highest Your Camera Can Do\n")

import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
from threading import Thread
import io
from PIL import Image
import os

HTML_FILE = 'index.html'
LIGHT_BLUE = '#ADD8E6'  # Hex code for light blue

class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open(HTML_FILE, 'rb') as file:
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, "HTML file not found")
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    ret, frame = capture.read()
                    if not ret:
                        break
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG')
                    frame_data = buffer.getvalue()
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(frame_data)))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print(f"Streaming error: {e}")
        else:
            self.send_error(404)
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def generate_html(width, height):
    return f"""
    <html>
    <head>
        <title>Camera Stream</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background-color: {LIGHT_BLUE}; /* Set background to light blue */
                font-family: sans-serif;
            }}
            .container {{
                text-align: center;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ccc;
                box-shadow: 2px 2px 5px #888888;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Live Camera Feed</h1>
            <img src="stream.mjpg" width="{width}" height="{height}" />
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    capture = cv2.VideoCapture(0)

    if not capture.isOpened():
        print("Error: Could not open camera.")
        exit()

    max_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    max_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, max_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, max_height)

    actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    try:
        with open(HTML_FILE, 'w') as f:
            f.write(generate_html(actual_width, actual_height))

        port = 9999
        server_address = ('', port)
        httpd = ThreadedHTTPServer(server_address, StreamingHandler)
        print(f"Serving at http://(AllIps):{port}/ at resolution: {actual_width}x{actual_height}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        capture.release()
        if 'httpd' in locals():
            httpd.shutdown()
            httpd.server_close()
        if os.path.exists(HTML_FILE):
            os.remove(HTML_FILE)
            print(f"Deleted file: {HTML_FILE}")
        print("Camera released and server stopped."),
