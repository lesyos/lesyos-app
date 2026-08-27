def ask_gemini(prompt_text, api_key):
    if not api_key:
        return "الرجاء إدخال مفتاح الـ API أولاً في الخانة المخصصة بالأعلى."

    history = get_history()
    context = "You are Lesyos, an advanced strategic AI partner. Respond naturally, directly, and concisely in Arabic.\n"
    for h in reversed(history):
        context += f"User: {h[0]}\nLesyos: {h[1]}\n"
    context += f"User: {prompt_text}\nLesyos:"

    # التحديث إلى gemini-3.6-flash
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
