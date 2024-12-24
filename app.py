import os
import time
import uuid
from flask import Flask, request, jsonify, redirect, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # ปรับ CORS ตามความเหมาะสม

# ตัวแปรเก็บข้อมูล
current_target = "https://docs.google.com/forms/d/e/1FAIpQLSehlUyC6Gqmt0EHQ48xZY83nHX2ibqwpYcS7u7o5Kgf1jnUEQ/viewform"  # URL เริ่มต้น
valid_tokens = {}
TOKEN_EXPIRY_TIME = 60  # เวลาให้ QR Code หมดอายุ (วินาที)


@app.route('/')
def index():
    """Route สำหรับหน้าเริ่มต้น"""
    return render_template("index.html")  # ใช้ render_template แสดงไฟล์ index.html


@app.route('/generate', methods=['POST'])
def generate_qr():
    """API สำหรับสร้าง QR Code ใหม่"""
    global current_target, valid_tokens

    # รับ URL ใหม่จาก Request Body
    new_target = request.json.get('new_target')
    if not new_target or not isinstance(new_target, str):
        return jsonify({"error": "กรุณาระบุ URL เป้าหมายที่ถูกต้อง"}), 400

    # ตรวจสอบ URL ให้แน่ใจว่าเป็น URL ที่ถูกต้อง
    if not new_target.startswith("http"):
        return jsonify({"error": "กรุณาระบุ URL ที่ถูกต้อง"}), 400

    # สร้าง Token ใหม่พร้อม timestamp
    token = str(uuid.uuid4())  # ใช้ UUID แทน time.time()
    valid_tokens[token] = {"target": new_target, "timestamp": time.time()}
    current_target = new_target

    return jsonify({
        "qr_url": f"https://qr-check-in-k1oj.onrender.com/redirect?token={token}",
        "message": "QR Code ใหม่ถูกสร้างเรียบร้อยแล้ว"
    })


@app.route('/redirect', methods=['GET'])
def redirect_to_target():
    """Route สำหรับ Redirect ด้วย Token"""
    token = request.args.get('token')
    if token in valid_tokens:
        # ตรวจสอบเวลา Token
        token_data = valid_tokens[token]
        if time.time() - token_data['timestamp'] < TOKEN_EXPIRY_TIME:
            return redirect(token_data['target'])
        else:
            del valid_tokens[token]  # ลบ Token หมดอายุ
            return render_expired_page()

    return render_expired_page()  # หาก Token ไม่ถูกต้อง


def render_expired_page():
    """ฟังก์ชันแสดงหน้า QR Code หมดอายุ"""
    return """
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QR Code หมดอายุ</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f9f9f9;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
            }
            h1 {
                color: #E74C3C;
                margin-bottom: 20px;
            }
            p {
                font-size: 18px;
                color: #555;
            }
            a {
                margin-top: 20px;
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #3498DB;
                border-radius: 5px;
                text-decoration: none;
                transition: background-color 0.3s ease;
            }
            a:hover {
                background-color: #2980B9;
            }
        </style>
    </head>
    <body>
       <h1>QR Code นี้หมดอายุ</h1>
        <p>โปรดสแกนใหม่อีกครั้ง</p>
        <a href="/">กลับไปยังหน้าแรก</a>
    </body>
    </html>
    """, 403


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
