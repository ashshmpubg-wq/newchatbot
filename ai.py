import logging

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, AI_MODEL, SYSTEM_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)

# Google 2026-yilda modellarni tez-tez almashtiradi/eskirtiradi (masalan 2.0
# seriyasi ko'p hollarda endi bepul tarifda kvota-siz qolgan, 3.x preview
# modellar esa ko'pincha bepul tarifga umuman kirmaydi). Shuning uchun avval
# hozircha eng barqaror bepul modellarni sinaymiz, keyin kerak bo'lsa
# avtomatik boshqasiga o'tamiz.
PREFERRED_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]
BAD_KEYWORDS = ("1.0", "1.5", "2.0", "preview", "exp", "image", "audio", "vision", "embedding", "thinking")

_working_model = None
_bad_models: set[str] = set()


def _list_candidate_models() -> list[str]:
    try:
        names = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if "generateContent" in actions:
                names.append(name)
        return names
    except Exception as e:
        logging.error(f"[AI-ERROR] Modellar ro'yxatini olishda xato: {e}")
        return []


def _next_candidate() -> str:
    if AI_MODEL and AI_MODEL not in _bad_models:
        return AI_MODEL

    all_names = _list_candidate_models()

    for preferred in PREFERRED_MODELS:
        if preferred in all_names and preferred not in _bad_models:
            return preferred

    filtered = [
        n for n in all_names
        if n not in _bad_models and "flash" in n.lower()
        and not any(bad in n.lower() for bad in BAD_KEYWORDS)
    ]
    lite = [n for n in filtered if "lite" in n]
    ordered = lite + [n for n in filtered if n not in lite]
    return ordered[0] if ordered else "gemini-2.5-flash-lite"


async def generate_reply(user_message: str, extra_context: str = "") -> str:
    """Google Gemini API orqali (bepul) mijozning xabariga javob generatsiya qiladi.
    Model eskirgan/kvotasi tugagan bo'lsa, avtomatik boshqa modelga o'tadi."""
    global _working_model

    system_instruction = SYSTEM_PROMPT
    if extra_context:
        system_instruction = f"{SYSTEM_PROMPT}\n\n{extra_context}"

    for _ in range(3):
        model_name = _working_model or _next_candidate()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=400,
                ),
            )
            _working_model = model_name
            logging.info(f"[AI] Ishlayotgan model: {model_name}")
            return response.text
        except Exception as e:
            error_text = str(e)
            logging.error(f"[AI-ERROR] {model_name}: {type(e).__name__}: {error_text}")
            if any(code in error_text for code in ("RESOURCE_EXHAUSTED", "429", "404", "NOT_FOUND")):
                _bad_models.add(model_name)
                _working_model = None
                continue
            break

    return "Kechirasiz, hozir javob bera olmayapman. Tez orada o'zim yozaman."