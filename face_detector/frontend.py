from flask import Flask, render_template_string
from backend import register_backend_routes

app = Flask(__name__)

html_template = """
<!doctype html>
<html>
<head>
  <title>ESP32-CAM Face Detection Stream</title>
  <style>
    body { font-family: Arial, sans-serif; text-align:center; margin-top:20px; background:#fafafa; }
    #video { border: 3px solid #222; max-width: 90%; height: auto; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.4); }
  </style>
</head>
<body>
  <h2>Smart Light with Face Detection</h2>
  <div>
    <img id="video" src="/video_feed" alt="Stream loading..." />
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

# Đăng ký backend routes
register_backend_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, threaded=True)