import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Get GapGPT API Key from environment variables
GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")
GAPGPT_BASE_URL = os.getenv("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1")

def analyze_vitals_with_ai(vitals_data_text, is_session=False, lang='fa'):
    """
    Sends vital signs data to GapGPT using their official SDK client wrapper.
    Returns health analysis as a dictionary containing both 'fa' and 'en' keys.
    """
    if not GAPGPT_API_KEY:
        return {
            "fa": "کلید API مربوط به GapGPT تنظیم نشده است. لطفا فایل .env را بررسی کنید.",
            "en": "GAPGPT_API_KEY is not set in the .env file!"
        }

    context_desc = "a recent measurement session" if is_session else "a specific time period"
    prompt = f"""
        You are an intelligent medical vital signs analysis assistant.
        Analyze the following patient vital signs data ({context_desc}):
        {vitals_data_text}
    
        Return your response strictly as a VALID, RAW JSON object with no markdown formatting around it (no ```json wrappers, just raw braces).
        Follow this exact JSON structure:
        {{
            "fa": "۱. میانگین و وضعیت کلی: ...\\n۲. آنومالی یا نوسان شدید: ...\\n۳. توصیه اولیه پزشکی: ...",
            "en": "1. Overall Status & Average: ...\\n2. Anomalies/Spikes: ...\\n3. Initial Medical Advice: ..."
        }}"""

    try:
        # Initialize OpenAI client with GapGPT configurations
        client = OpenAI(
            api_key=GAPGPT_API_KEY,
            base_url=GAPGPT_BASE_URL
        )

        # Call the custom responses creator endpoint provided by GapGPT
        response = client.responses.create(
            model="gapgpt-qwen-3.6",
            input=prompt
        )

        content = response.output_text.strip()
        
        # Clean markdown formatting if present
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        # Parse JSON output
        data = json.loads(content)
        return {
            "fa": data.get("fa", "تحلیلی دریافت نشد."),
            "en": data.get("en", "No analysis received.")
        }
    except json.JSONDecodeError:
        # Fallback to displaying raw content in both languages if JSON parsing fails
        return {
            "fa": content,
            "en": content
        }
    except Exception as e:
        print(f"Error connecting to GapGPT: {str(e)}")
        err_msg = f"Error receiving response from AI: {str(e)}"
        return {
            "fa": 'خطا در دریافت پاسخ از هوش مصنوعی (GapGPT)',
            "en": err_msg
        }