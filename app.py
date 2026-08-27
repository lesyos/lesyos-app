from flask import Flask, render_template_string, request, jsonify, session
import requests
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# قاعدة بيانات مؤقتة للذاكرة
CHAT_HISTORY = []

def save_memory(user_msg, ai_msg):
    CHAT_HISTORY.append((user_msg, ai_msg))
    if len(CHAT_HISTORY) > 20:
        CHAT_HISTORY.pop(0)

def get_history():
    return CHAT_HISTORY

def ask_gemini(prompt_text, api_key):
    if not api_key:
        return "الرجاء إدخال مفتاح الـ API أولاً في الخانة المخصصة بالأعلى."

    history = get_history()
    context = "You are Lesyos, an advanced strategic AI partner. Respond naturally, directly, and concisely in Arabic.\n"
    for h in reversed(history):
        context += f"User: {h[0]}\nLesyos: {h[1]}\n"
    context += f"User: {prompt_text}\nLesyos:"

    # الاستدعاء المباشر لـ gemini-3.6-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": context}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        data = res.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            reply = data['candidates'][0]['content']['parts'][0]['text']
            save_memory(prompt_text, reply)
            return reply
        elif 'error' in data:
            return f"خطأ API: {data['error'].get('message', 'تأكد من صحة المفتاح')}"
        else:
            return "لم يتم استلام رد، حاول مجدداً."
    except Exception as e:
        return f"خطأ شبكة: {str(e)}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LESYOS AI ENGINE</title>
    <style>
        body { background-color: #050b14; color: #ffffff; font-family: sans-serif; margin: 0; padding: 15px; display: flex; flex-direction: column; height: 95vh; }
        h2 { text-align: center; color: #2196F3; margin-bottom: 10px; font-size: 20px; }
        .api-box { display: flex; gap: 8px; margin-bottom: 15px; }
        .api-box input { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #1a2a40; background: #0b172a; color: #fff; text-align: center; }
        .api-box button { padding: 10px 15px; background: #2196F3; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        .chat-box { flex: 1; overflow-y: auto; border: 1px solid #1a2a40; padding: 10px; border-radius: 8px; background: #08101d; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px 14px; border-radius: 8px; max-width: 85%; word-wrap: break-word; font-size: 14px; line-height: 1.4; }
        .user { background: #0d47a1; align-self: flex-start; text-align: left; direction: ltr; }
        .ai { background: #101f38; align-self: flex-end; border: 1px solid #1a2a40; }
        .input-box { display: flex; gap: 8px; }
        .input-box input { flex: 1; padding: 12px; border-radius: 5px; border: 1px solid #1a2a40; background: #0b172a; color: #fff; }
        .input-box button { padding: 12px 20px; background: #2196F3; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <h2>LESYOS AI ENGINE</h2>
    
    <div class="api-box">
        <input type="password" id="apiKey" placeholder="أدخل Gemini API Key هنا..." value="{{ session.get('api_key', '') }}">
        <button onclick="saveKey()">حفظ</button>
    </div>

    <div class="chat-box" id="chatBox"></div>

    <div class="input-box">
        <input type="text" id="userInput" placeholder="اكتب رسالتك..." onkeypress="if(event.key==='Enter') sendMsg()">
        <button onclick="sendMsg()">إرسال</button>
    </div>

    <script>
        function saveKey() {
            const key = document.getElementById('apiKey').value;
            fetch('/set_key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key: key})
            }).then(() => alert('تم حفظ المفتاح!'));
        }

        async function sendMsg() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if(!msg) return;

            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `<div class="msg user">${msg}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            const data = await res.json();
            
            chatBox.innerHTML += `<div class="msg ai">${data.response}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_key', methods=['POST'])
def set_key():
    data = request.get_json()
    session['api_key'] = data.get('key', '')
    return jsonify({'status': 'ok'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get('message', '')
    api_key = session.get('api_key', '')
    
    reply = ask_gemini(user_msg, api_key)
    return jsonify({'response': reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
