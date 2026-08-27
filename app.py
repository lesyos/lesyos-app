import os
import sqlite3
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('lesyos_web_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            ai_response TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect('lesyos_web_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, ai_response FROM memory ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_memory(user_input, ai_response):
    conn = sqlite3.connect('lesyos_web_memory.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()
    conn.close()

def ask_gemini(prompt_text, api_key):
    if not api_key:
        return "الرجاء إدخال مفتاح الـ API أولاً في الخانة المخصصة بالأعلى."

    history = get_history()
    context = "You are Lesyos, an advanced strategic AI partner. Respond naturally, directly, and concisely in Arabic.\n"
    for h in reversed(history):
        context += f"User: {h[0]}\nLesyos: {h[1]}\n"
    context += f"User: {prompt_text}\nLesyos:"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": context}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        data = res.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            reply = data['candidates'][0]['content']['parts'][0]['text']
            save_memory(prompt_text, reply)
            return reply
        else:
            return f"Error: {data.get('error', {}).get('message', 'Invalid API Key')}"
    except Exception as e:
        return f"Network Error: {str(e)}"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lesyos Dynamic Voice Web</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; margin: 0; padding: 15px; }
        .container { max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; height: 92vh; }
        .header { text-align: center; padding: 10px; font-weight: bold; color: #38bdf8; font-size: 1.2rem; border-bottom: 1px solid #334155; }
        .api-box { display: flex; gap: 8px; padding: 10px 0; border-bottom: 1px solid #334155; }
        .api-box input { font-size: 0.8rem; flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #334155; background: #1e293b; color: white; }
        .api-box button { padding: 8px 12px; border-radius: 6px; border: none; background: #0284c7; color: white; cursor: pointer; }
        .chat-box { flex: 1; overflow-y: auto; padding: 10px 0; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 12px 16px; border-radius: 12px; max-width: 80%; line-height: 1.5; font-size: 0.95rem; }
        .user { align-self: flex-start; background-color: #0284c7; color: white; }
        .ai { align-self: flex-end; background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155; }
        .input-area { display: flex; gap: 8px; padding-top: 10px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: white; outline: none; }
        button { padding: 12px 16px; border-radius: 8px; border: none; background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        .btn-mic { background: #e11d48; }
        .btn-mic.listening { background: #22c55e; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">LESYOS AI ENGINE</div>
        <div class="api-box">
            <input type="password" id="apiKeyInput" placeholder="أدخل Gemini API Key هنا...">
            <button onclick="saveKey()">حفظ</button>
        </div>
        <div class="chat-box" id="chatBox"></div>
        <div class="input-area">
            <button id="micBtn" class="btn-mic" onclick="toggleVoice()">🎤</button>
            <input type="text" id="userInput" placeholder="اكتب أو تحدث بالمايك..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button onclick="sendMsg()">إرسال</button>
        </div>
    </div>
    <script>
        document.getElementById('apiKeyInput').value = localStorage.getItem('lesyos_key') || '';

        function saveKey() {
            const key = document.getElementById('apiKeyInput').value.trim();
            localStorage.setItem('lesyos_key', key);
            alert('تم حفظ مفتاح الـ API بنجاح في المتصفح!');
        }

        let recognition;
        let isListening = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'ar-SA';

            recognition.onresult = (event) => {
                document.getElementById('userInput').value = event.results[0][0].transcript;
                stopVoice();
                sendMsg();
            };
            recognition.onerror = () => stopVoice();
            recognition.onend = () => stopVoice();
        }

        function toggleVoice() {
            if (!recognition) { alert("المتصفح لا يدعم الصوت"); return; }
            if (isListening) { stopVoice(); } 
            else {
                recognition.start();
                isListening = true;
                document.getElementById('micBtn').classList.add('listening');
            }
        }

        function stopVoice() {
            if (recognition && isListening) { recognition.stop(); }
            isListening = false;
            document.getElementById('micBtn').classList.remove('listening');
        }

        function speakText(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ar-SA';
                window.speechSynthesis.speak(utterance);
            }
        }

        async function sendMsg() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const apiKey = localStorage.getItem('lesyos_key') || document.getElementById('apiKeyInput').value.trim();
            const text = input.value.trim();

            if (!text) return;
            if (!apiKey) {
                alert('يرجى إدخال مفتاح الـ API في الأعلى والضغط على حفظ.');
                return;
            }

            chatBox.innerHTML += `<div class="msg user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text, api_key: apiKey})
            });
            const data = await res.json();
            chatBox.innerHTML += `<div class="msg ai">${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            speakText(data.reply);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    api_key = data.get('api_key', '')
    reply = ask_gemini(user_msg, api_key)
    return jsonify({'reply': reply})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
