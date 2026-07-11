import aiosqlite
from config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # ---------- Umumiy foydalanuvchilar ----------
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # ---------- Majburiy obuna (shaxsiy chat uchun) ----------
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                title TEXT,
                username TEXT,
                invite_link TEXT,
                chat_type TEXT
            )
        """)
        # ---------- To'lovli kategoriyalar ----------
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price TEXT,
                payment_link TEXT,
                channel_link TEXT,
                info TEXT DEFAULT ''
            )
        """)
        # Eski bazalarda "info" ustuni bo'lmasligi mumkin - qo'shib qo'yamiz
        try:
            await db.execute("ALTER TABLE categories ADD COLUMN info TEXT DEFAULT ''")
            await db.commit()
        except Exception:
            pass  # ustun allaqachon mavjud
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                screenshot_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # ---------- Guruh boshqaruvi ----------
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                welcome_text TEXT DEFAULT '👋 Xush kelibsiz, {name}!',
                mandatory_chat_id INTEGER,
                mandatory_chat_link TEXT,
                mandatory_chat_title TEXT,
                link_filter_enabled INTEGER DEFAULT 1,
                flood_filter_enabled INTEGER DEFAULT 1,
                swear_filter_enabled INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_words (
                chat_id INTEGER,
                word TEXT,
                PRIMARY KEY (chat_id, word)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                mandatory_chat_id INTEGER,
                mandatory_chat_link TEXT,
                mandatory_chat_title TEXT
            )
        """)
        # ---------- Avtomatik takroriy reklama ----------
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_chat_id INTEGER,
                source_message_id INTEGER,
                send_time TEXT,
                target TEXT,
                last_sent_date TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        await db.commit()


# ============================================================
# FOYDALANUVCHILAR
# ============================================================

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]


async def users_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


# ============================================================
# MAJBURIY OBUNA KANALLARI (shaxsiy chat)
# ============================================================

async def add_channel(chat_id: int, title: str, username: str, invite_link: str, chat_type: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT OR REPLACE INTO channels (chat_id, title, username, invite_link, chat_type)
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, title, username, invite_link, chat_type)
        )
        await db.commit()


async def remove_channel(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_channels():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT chat_id, title, username, invite_link, chat_type FROM channels"
        )
        return await cursor.fetchall()


async def channels_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM channels")
        return (await cursor.fetchone())[0]


# ============================================================
# TO'LOVLI KATEGORIYALAR
# ============================================================

async def add_category(name: str, price: str, payment_link: str, channel_link: str, info: str = ""):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO categories (name, price, payment_link, channel_link, info)
               VALUES (?, ?, ?, ?, ?)""",
            (name, price, payment_link, channel_link, info)
        )
        await db.commit()
        return cursor.lastrowid


async def get_categories():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, name, price, payment_link, channel_link, info FROM categories"
        )
        return await cursor.fetchall()


async def get_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, name, price, payment_link, channel_link, info FROM categories WHERE id = ?",
            (category_id,)
        )
        return await cursor.fetchone()


async def remove_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()


async def create_request(user_id: int, category_id: int, screenshot_file_id: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO requests (user_id, category_id, screenshot_file_id, status)
               VALUES (?, ?, ?, 'pending')""",
            (user_id, category_id, screenshot_file_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_request(request_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, user_id, category_id, screenshot_file_id, status FROM requests WHERE id = ?",
            (request_id,)
        )
        return await cursor.fetchone()


async def update_request_status(request_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
        await db.commit()


# ============================================================
# GURUHLAR
# ============================================================

async def register_group(chat_id: int, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO groups (chat_id, title) VALUES (?, ?)", (chat_id, title))
        await db.execute("UPDATE groups SET title = ? WHERE chat_id = ?", (title, chat_id))
        await db.commit()


async def unregister_group(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM custom_words WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_group(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        return await cursor.fetchone()


async def get_all_groups():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT chat_id FROM groups")
        return [row[0] for row in await cursor.fetchall()]


async def groups_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM groups")
        return (await cursor.fetchone())[0]


async def set_welcome_text(chat_id: int, text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE groups SET welcome_text = ? WHERE chat_id = ?", (text, chat_id))
        await db.commit()


async def set_mandatory_chat(chat_id: int, mandatory_chat_id: int, link: str, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """UPDATE groups SET mandatory_chat_id = ?, mandatory_chat_link = ?,
               mandatory_chat_title = ? WHERE chat_id = ?""",
            (mandatory_chat_id, link, title, chat_id)
        )
        await db.commit()


async def remove_mandatory_chat(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """UPDATE groups SET mandatory_chat_id = NULL, mandatory_chat_link = NULL,
               mandatory_chat_title = NULL WHERE chat_id = ?""",
            (chat_id,)
        )
        await db.commit()


async def toggle_filter(chat_id: int, column: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(f"SELECT {column} FROM groups WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        new_value = 0 if (row and row[0]) else 1
        await db.execute(f"UPDATE groups SET {column} = ? WHERE chat_id = ?", (new_value, chat_id))
        await db.commit()
        return bool(new_value)


async def add_custom_word(chat_id: int, word: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO custom_words (chat_id, word) VALUES (?, ?)",
            (chat_id, word.lower())
        )
        await db.commit()


async def remove_custom_word(chat_id: int, word: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM custom_words WHERE chat_id = ? AND word = ?", (chat_id, word.lower()))
        await db.commit()


async def get_custom_words(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT word FROM custom_words WHERE chat_id = ?", (chat_id,))
        return [row[0] for row in await cursor.fetchall()]


async def set_global_mandatory(chat_id: int, link: str, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO global_settings (id, mandatory_chat_id, mandatory_chat_link, mandatory_chat_title)
               VALUES (1, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   mandatory_chat_id = excluded.mandatory_chat_id,
                   mandatory_chat_link = excluded.mandatory_chat_link,
                   mandatory_chat_title = excluded.mandatory_chat_title""",
            (chat_id, link, title)
        )
        await db.commit()


async def remove_global_mandatory():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM global_settings WHERE id = 1")
        await db.commit()


async def get_global_mandatory():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM global_settings WHERE id = 1")
        return await cursor.fetchone()


# ============================================================
# AVTOMATIK TAKRORIY REKLAMA
# ============================================================

async def add_scheduled_ad(source_chat_id: int, source_message_id: int, send_time: str, target: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO scheduled_ads (source_chat_id, source_message_id, send_time, target)
               VALUES (?, ?, ?, ?)""",
            (source_chat_id, source_message_id, send_time, target)
        )
        await db.commit()
        return cursor.lastrowid


async def get_scheduled_ads():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM scheduled_ads")
        return await cursor.fetchall()


async def remove_scheduled_ad(ad_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM scheduled_ads WHERE id = ?", (ad_id,))
        await db.commit()


async def mark_scheduled_ad_sent(ad_id: int, date_str: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE scheduled_ads SET last_sent_date = ? WHERE id = ?", (date_str, ad_id))
        await db.commit()


async def toggle_scheduled_ad(ad_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT enabled FROM scheduled_ads WHERE id = ?", (ad_id,))
        row = await cursor.fetchone()
        new_value = 0 if (row and row[0]) else 1
        await db.execute("UPDATE scheduled_ads SET enabled = ? WHERE id = ?", (new_value, ad_id))
        await db.commit()
        return bool(new_value)