# Universal Bot (barcha funksiyalar bitta botda)

Bu — avval alohida qurgan botlarimizning **birlashtirilgan versiyasi**
(kino-kod tizimisiz):

1. 🔐 **Majburiy obuna** (shaxsiy chatda `/start`)
2. 🛍 **To'lovli kategoriyalar** (Click/Payme + chek tasdiqlash)
3. 🤖 **AI avtoresponder** (Telegram Business — band bo'lganingizda javob beradi)
4. 👥 **Guruh boshqaruvi** (xush kelibsiz, so'kinish/havola/flood filtri, majburiy obuna, reklama)

Hammasi **bitta bot token**, **bitta baza**, **bitta GitHub Actions** orqali ishlaydi.

## 1-qadam: Sozlash

`config.py`da to'ldiring:
```python
BOT_TOKEN = "SIZNING_BOT_TOKENINGIZ"
ADMIN_IDS = [SIZNING_TELEGRAM_ID]        # @userinfobot orqali bilib oling
GEMINI_API_KEY = "SIZNING_GEMINI_KALITINGIZ"   # aistudio.google.com (bepul)
```

`SYSTEM_PROMPT` va `DEFAULT_SWEAR_WORDS`ni ham xohlaganingizcha moslang.

## 2-qadam: Telegram Business yoqish (AI avtoresponder uchun)

@BotFather → `/mybots` → botingiz → **Bot Settings** → **Business Mode** → **Turn on**

Keyin Telegram ilovasida: **Sozlamalar → Telegram Business → Chatbots** →
bot username'ini qo'shing.

## 3-qadam: O'rnatish va ishga tushirish

```bash
pip install -r requirements.txt
python main.py
```

## Admin panel

Botga **shaxsiy xabar** orqali `/admin` yozing — tugmali panel ochiladi:

- 📢 **Majburiy obuna kanallari** — qo'shish/ro'yxat/o'chirish
- 🛍 **To'lov kategoriyalari** — qo'shish (nomi→narxi→to'lov ma'lumoti→kanal
  linki)/ro'yxat/o'chirish
- 👥 **Guruhlar boshqaruvi** — global majburiy obuna, guruhlarga reklama
  yuborish
- 📨 **Foydalanuvchilarga xabar** — shaxsiy chatdagi barcha foydalanuvchilarga
- 📊 **Umumiy statistika**

## Guruh ichida (guruh adminlari uchun)

Botni guruhga **admin** qilib qo'shing, so'ng guruh ichida yozing: `/settings`
— bu yerdan barcha buyruqlar ko'rinadi (`/setwelcome`, `/setsub`,
`/togglelinks` va h.k.)

## GitHub'da doimiy ishlatish

Avvalgi botlarimiz bilan bir xil tartib:
1. Repo yarating, barcha fayllarni **papka tuzilmasi bilan** yuklang
2. Repo'ni public qiling
3. Actions'dan **"Run Universal Bot"**ni ishga tushiring

Har qanday o'zgarish (kanal, kategoriya, guruh sozlamasi) avtomatik ravishda
`database.db` orqali GitHub'ga saqlanadi — 5 soatlik qayta ishga tushishlarda
hech narsa yo'qolmaydi.

## Loyiha tuzilmasi

```
universal_bot/
├── main.py
├── config.py
├── database.py
├── keyboards.py
├── ai.py
├── git_sync.py
├── requirements.txt
├── .github/workflows/bot.yml
└── handlers/
    ├── __init__.py
    ├── start.py         — shaxsiy chat: majburiy obuna + do'kon
    ├── admin_panel.py    — yagona /admin panel (hammasi shu yerda)
    ├── business.py       — Telegram Business AI avtoresponder
    ├── group.py          — guruh moderatsiyasi
    └── group_admin.py    — guruh ichidagi admin buyruqlari
```

## Eslatma

- Avvalgi 4 ta alohida botingiz (agar hali GitHub'da ishlab tursa) endi
  ortiqcha — xohlasangiz ularni to'xtatib (Actions'ni o'chirib), shu yagona
  botga o'tishingiz mumkin.
- Kino-kod tizimi bu birlashtirilgan botga **kiritilmagan** (alohida bot
  sifatida qoladi).
