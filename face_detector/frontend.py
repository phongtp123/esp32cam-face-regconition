from flask import Flask, render_template_string
from backend import register_backend_routes

app = Flask(__name__)

html_template = """
<!doctype html>
<html>
<head>
  <title>ESP32-CAM</title>
  <style>
    body { font-family: Arial, sans-serif; text-align:center; margin-top:20px; background:#fafafa; }
    #video { border: 3px solid #222; max-width: 90%; height: auto; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.4); }
    #logs { max-height:500px; overflow-y:scroll; text-align:left; margin:20px auto; width:30%; padding:10px; border:1px solid #ccc; background:#fff; border-radius:5px; }
    button { margin:5px; padding:10px 20px; font-size:16px; cursor:pointer; border-radius:5px; border:none; background:#007BFF; color:#fff; }
    button:hover { background:#0056b3; }
  </style>
</head>
<body>
  <h2>ESP32-CAM</h2>
  <div>
    <img id="video" src="/video_feed" alt="Stream loading..." />
  </div>
  <div>
    <button onclick="setMode('strict')">Strict Mode</button>
    <button onclick="setMode('non-strict')">Non-Strict Mode</button>
  </div>
  <div id="logs"></div>

  <script>
    // --- Gửi request đổi chế độ ---
    function setMode(mode) {
      fetch(`/set_mode/${mode}`)
        .then(res => res.json())
        .then(data => {
          document.getElementById('video').src = '/video_feed?' + new Date().getTime();
        })
        .catch(err => appendLog(`Error switching mode: ${err}`));
    }

    // --- Append log vào div ---
    function appendLog(msg) {
      const logDiv = document.getElementById('logs');
      const p = document.createElement('div');
      p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
      logDiv.appendChild(p);
      logDiv.scrollTop = logDiv.scrollHeight;
    }

    // --- SSE cho log realtime ---
    const eventSource = new EventSource('/init_log');
    eventSource.onmessage = function(event) {
      // Nếu backend gửi lệnh CLEAR
      if(event.data === "CLEAR" || event.data === "DONE") {
        document.getElementById('logs').innerHTML = '';
        return;
      }
      appendLog(event.data);
    };
    eventSource.onerror = function(err) {
      appendLog("SSE connection lost.");
      eventSource.close();
    };
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
