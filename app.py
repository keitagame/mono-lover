from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

PORT = 8000
FILE_NAME = "post.txt"

HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Simple Chat</title>

<style>
body{
    font-family:sans-serif;
    background:#111;
    color:white;
    margin:0;
    padding:20px;
}

#messages{
    display:flex;
    flex-direction:column;
    gap:10px;
    margin-bottom:20px;
}

.msg{
    background:#222;
    padding:10px;
    border-radius:10px;
    max-width:400px;
}

.row{
    display:flex;
    gap:10px;
}

input{
    flex:1;
    padding:10px;
}

button{
    padding:10px 20px;
}
</style>
</head>
<body>

<h1>Chat</h1>

<div id="messages"></div>

<div class="row">
    <input id="text" placeholder="message">
    <button onclick="send()">送信</button>
</div>

<script>

async function loadMessages(){
    const res = await fetch("/messages");
    const data = await res.json();

    const container = document.getElementById("messages");
    container.innerHTML = "";

    data.messages.forEach(msg => {
        const div = document.createElement("div");
        div.className = "msg";
        div.textContent = msg;
        container.appendChild(div);
    });

    window.scrollTo(0, document.body.scrollHeight);
}

async function send(){
    const input = document.getElementById("text");
    const message = input.value.trim();

    if(!message) return;

    await fetch("/post", {
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            message
        })
    });

    input.value = "";

    loadMessages();
}

setInterval(loadMessages, 1000);

loadMessages();

</script>

</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):

    def send_json(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(
            json.dumps(obj).encode("utf-8")
        )

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):

        # HTML表示
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write(
                HTML.encode("utf-8")
            )
            return

        # メッセージ取得
        if self.path == "/messages":

            if not os.path.exists(FILE_NAME):
                open(FILE_NAME, "w", encoding="utf-8").close()

            with open(FILE_NAME, "r", encoding="utf-8") as f:
                lines = [
                    line.rstrip("\\n")
                    for line in f
                ]

            self.send_json({
                "messages": lines
            })
            return

        self.send_error(404)

    def do_POST(self):

        # メッセージ投稿
        if self.path == "/post":

            content_length = int(
                self.headers["Content-Length"]
            )

            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)

                message = data.get("message", "")

                message = message.replace("\\n", " ")

                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(message + "\\n")

                self.send_json({
                    "status": "ok"
                })

            except Exception as e:
                self.send_error(500, str(e))

            return

        self.send_error(404)

if __name__ == "__main__":

    server = HTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )

    print(f"http://localhost:{PORT}")

    server.serve_forever()
