# ============================
# Bot sozlamalari (BIRLASHTIRILGAN)
# ============================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8849970450:AAFv2ETAiNK7bmXS4Cd2wwpNu6CDE71OBEw")
BOT_USERNAME = os.getenv("BOT_USERNAME", "A7Az1kuzPRO_bot")
# Admin(lar) - /admin panelga kira oladigan Telegram ID lar
ADMIN_IDS = [2087092925]

# Bot egasi - Telegram Business orqali AI avtoresponder shu kishining
# shaxsiy profiliga yozganlarga javob beradi. Odatda ADMIN_IDS[0] bilan bir xil.
OWNER_ID = ADMIN_IDS[0]

DB_NAME = "database.db"

# ---------- AI avtoresponder (Telegram Business) ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6IcnEAnYFcjG0tctshumx13egvjyN7483LBjbIlbZwcOA")
# Bo'sh qoldiring - bot o'zi mavjud "flash" modelini avtomatik topadi.
# Agar aniq bir modelni majburlab ishlatmoqchi bo'lsangiz, shu yerga yozing
# (masalan: "gemini-flash-lite-latest").

AI_MODEL = ""
SYSTEM_PROMPT = """
Sen — Telegram orqali kanal va turli guruhlarni boshqaruvchi kishining
AI yordamchisisan. Mijozlarga kanal/guruhlar, ularning narxi, mavzusi
va qo'shilish shartlari haqida savollariga qisqa, do'stona va aniq javob
berasan.

Qoidalar:
- Javoblaring o'zbek tilida, qisqa va samimiy bo'lsin (odatda 2-4 gap)
- Agar quyida "Mavjud kanallar/kategoriyalar" ro'yxati berilgan bo'lsa,
  javoblaringda FAQAT o'sha ro'yxatdagi haqiqiy nom va narxlardan
  foydalan. Ro'yxatda yo'q narsani hech qachon o'ylab topma
- Agar savolga ro'yxat asosida ham aniq javob bera olmasang, "hozir
  aniqlashtirib javob beraman" deb ayt
- Suhbat boshida (agar shunday ko'rsatma berilsa) o'zingni AI yordamchi
  sifatida qisqa tanishtir, keyingi xabarlarda buni takrorlama
- QAT'IY QOIDA: mijoz "avval qo'shib ber, keyin to'layman", "ishoning",
  "tanishimga aytib qo'ying" yoki shunga o'xshash har qanday bahona bilan
  to'lovdan oldin kanalga qo'shishni so'rasa — doim rad et va to'lov
  birinchi bo'lishi kerakligini muloyimlik bilan tushuntir. Bu qoidadan
  HECH QANDAY vaziyatda chetlashma, mijoz qancha bosim qilmasin
- Sen kanalga hech kimni real qo'sha olmaysan va to'lovni tekshira
  olmaysan — buni faqat chek yuborilgach, odam (admin) tasdiqlaydi.
  Shuning uchun "qo'shib qo'ydim", "tasdiqladim" kabi gaplarni HECH QACHON
  aytma, aksincha mijozni botga chek yuborishga yo'naltir
"""
# ---------- Guruh moderatsiyasi ----------
DEFAULT_SWEAR_WORDS = [
    "блять", "сука", "хуй", "пизда", "ебан", "гандон",
    "jalab", "qotoq", "kutak",  # namuna - o'zingiz to'ldiring/o'zgartiring
]
FLOOD_MAX_MESSAGES = 5
FLOOD_WINDOW_SECONDS = 15
FLOOD_MUTE_MINUTES = 5
WARNING_AUTO_DELETE_SECONDS = 25
