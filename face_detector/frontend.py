from flask import Flask, render_template_string
from backend import register_backend_routes

app = Flask(__name__)

html_template = """
<!doctype html>
<html>
<head>
  <title>ESP32-CAM Face Detection Stream</title>
  <style>
    body { font-family: Arial, sans-serif; text-align:center; margin-top:20px; }
    #video { border: 2px solid #444; max-width: 90%; height: auto; }
    .btn { padding: 8px 14px; margin: 8px; cursor: pointer; border-radius:6px; border:1px solid #666; background:#eee; }
  </style>
</head>
<body>
  <h2>ESP32-CAM — Face Detection (Server-side)</h2>
  <div>
    <button class="btn" onclick="startStream()">Start Stream</button>
    <button class="btn" onclick="stopStream()">Stop Stream</button>
  </div>
  <div>
    <img id="video" src="" alt="Stream will appear here">
  </div>

  <script>
    const video = document.getElementById('video');
    function startStream(){
      video.src = "/video_feed";
    }
    function stopStream(){
      video.src = "";
      fetch('/stop_capture').catch(()=>{});
    }
  </script>
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