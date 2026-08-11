import os
import json
from dotenv import load_dotenv
import together

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

def analyze_vitals_with_ai(vitals_data_text, is_session=False, lang='fa'):
    """
    Sends vital signs data to Together AI (Qwen2.5 model) via SOCKS5 Proxy.
    Returns health analysis as a dictionary containing both 'fa' and 'en' keys.
    """
    if not TOGETHER_API_KEY:
        return {"error": "TOGETHER_API_KEY is not set in the .env file!"}

    proxy_url = os.getenv("HTTP_PROXY", "socks5://192.168.132.50:10301")
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    os.environ["ALL_PROXY"] = proxy_url

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

    messages = [
        {
            "role": "system",
            "content": "You are a helpful medical assistant that strictly outputs raw JSON."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        client = together.Together(api_key=TOGETHER_API_KEY)
        
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct-Turbo",
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        
        return {
            "fa": data.get("fa", "تحلیلی دریافت نشد."),
            "en": data.get("en", "No analysis received.")
        }

    except json.JSONDecodeError:
        return {"fa": content, "en": content}
    except Exception as e:
        print(f"Error connecting to Together AI: {str(e)}")
        err_msg = f"Error receiving response from AI: {str(e)}"
        return {"fa": err_msg, "en": err_msg}