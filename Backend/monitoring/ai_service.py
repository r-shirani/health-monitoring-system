import os
import json
from dotenv import load_dotenv
import together
import requests

load_dotenv()

# TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def analyze_vitals_with_ai(vitals_data_text, is_session=False, lang='fa'):
    """
    Sends vital signs data to Together AI (Qwen2.5 model) via SOCKS5 Proxy.
    Returns health analysis as a dictionary containing both 'fa' and 'en' keys.
    """
    if not GEMINI_API_KEY:
        return {"error": "TOGETHER_API_KEY is not set in the .env file!"}

    proxy_url = os.getenv("HTTP_PROXY", "socks5://192.168.132.50:10301")
    # os.environ["HTTP_PROXY"] = proxy_url
    # os.environ["HTTPS_PROXY"] = proxy_url
    # os.environ["ALL_PROXY"] = proxy_url
    proxies = None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    context_desc = "a recent measurement session" if is_session else "a specific time period"

    prompt = f"""
    You are an intelligent medical vital signs analysis assistant.
    Analyze the following patient vital signs data ({context_desc}):
    {vitals_data_text}

    Return your response strictly as a VALID JSON object with no markdown formatting around it.
    Follow this exact JSON structure:
    {{
        "fa": "۱. میانگین و وضعیت کلی: ...\\n۲. آنومالی یا نوسان شدید: ...\\n۳. توصیه اولیه پزشکی: ...",
        "en": "1. Overall Status & Average: ...\\n2. Anomalies/Spikes: ...\\n3. Initial Medical Advice: ..."
    }}
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=15)
        response.raise_for_status()
        
        response_data = response.json()
        
        raw_text_content = response_data['candidates']['content']['parts']['text']
        
        data = json.loads(raw_text_content)
        
        return {
            "fa": data.get("fa", "تحلیلی دریافت نشد."),
            "en": data.get("en", "No analysis received.")
        }

    except requests.exceptions.RequestException as req_err:
        print(f"[Gemini API Error] Connection/HTTP issue: {str(req_err)}")
        return {
            "fa": "خطا در برقراری ارتباط با سرور هوش مصنوعی جیمینای. لطفاً وضعیت پروکسی سرور را بررسی کنید.",
            "en": f"Gemini API connection error: {str(req_err)}"
        }
    except (json.JSONDecodeError, KeyError, IndexError) as parse_err:
        print(f"[Gemini API Error] Parsing failed. Raw response was: {response.text if 'response' in locals() else 'None'}")
        return {
            "fa": "خطا در پردازش اطلاعات دریافتی از هوش مصنوعی.",
            "en": f"Parsing response failed: {str(parse_err)}"
        }
    except Exception as e:
        print(f"[Gemini API Error] Unexpected error: {str(e)}")
        return {
            "fa": "خطای غیرمنتظره در سیستم هوش مصنوعی.",
            "en": f"Unexpected error: {str(e)}"
        }