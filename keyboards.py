from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================
# FOYDALANUVCHI TOMONI
# ============================================================

def subscribe_keyboard(channels):
    builder = InlineKeyboardBuilder()
    for chat_id, title, username, invite_link, chat_type in channels:
        url = f"https://t.me/{username}" if username else invite_link
        builder.button(text=f"➕ {title}", url=url)
    builder.button(text="✅ Tekshirish", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()


def categories_keyboard(categories):
    builder = InlineKeyboardBuilder()
    for cat_id, name, price, payment_link, channel_link, info in categories:
        builder.button(text=f"{name} — {price}", callback_data=f"cat_{cat_id}")
    builder.adjust(1)
    return builder.as_markup()


def category_detail_keyboard(category_id: int, payment_link: str):
    builder = InlineKeyboardBuilder()
    if payment_link and payment_link.startswith(("http://", "https://")):
        builder.button(text="💳 Havola orqali to'lash", url=payment_link)
    builder.button(text="📤 Chek yuborish", callback_data=f"pay_{category_id}")
    builder.button(text="⬅️ Orqaga", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def admin_review_keyboard(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"approve_{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_{request_id}")
    builder.adjust(2)
    return builder.as_markup()


def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    return builder.as_markup()


# ============================================================
# ADMIN PANEL — YAGONA BOSH MENYU
# ============================================================

def main_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Majburiy obuna kanallari", callback_data="menu_channels")
    builder.button(text="🛍 To'lov kategoriyalari", callback_data="menu_categories")
    builder.button(text="👥 Guruhlar boshqaruvi", callback_data="menu_groups")
    builder.button(text="📨 Foydalanuvchilarga xabar", callback_data="admin_broadcast_users")
    builder.button(text="📊 Umumiy statistika", callback_data="admin_stats")
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Bosh menyu", callback_data="admin_back_main")
    return builder.as_markup()


# ---------- Majburiy obuna kanallari submenu ----------

def channels_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kanal/Guruh qo'shish", callback_data="admin_add_channel")
    builder.button(text="📃 Ro'yxat / o'chirish", callback_data="admin_list_channels")
    builder.button(text="⬅️ Bosh menyu", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def group_subscribe_keyboard(unmet: list[tuple[str, str]]):
    """unmet: [(link, title), ...] - guruhda obuna bo'lmagan kanal/guruhlar"""
    builder = InlineKeyboardBuilder()
    for link, title in unmet:
        builder.button(text=f"➕ {title}", url=link)
    builder.adjust(1)
    return builder.as_markup()


def channels_remove_keyboard(channels):
    builder = InlineKeyboardBuilder()
    for chat_id, title, username, invite_link, chat_type in channels:
        builder.button(text=f"🗑 {title}", callback_data=f"remove_ch_{chat_id}")
    builder.button(text="⬅️ Orqaga", callback_data="menu_channels")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Kategoriyalar submenu ----------

def categories_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kategoriya qo'shish", callback_data="admin_add_category")
    builder.button(text="📃 Ro'yxat / o'chirish", callback_data="admin_list_categories")
    builder.button(text="⬅️ Bosh menyu", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


def categories_remove_keyboard(categories):
    builder = InlineKeyboardBuilder()
    for cat_id, name, price, payment_link, channel_link, info in categories:
        builder.button(text=f"🗑 {name}", callback_data=f"remove_cat_{cat_id}")
    builder.button(text="⬅️ Orqaga", callback_data="menu_categories")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Guruhlar boshqaruvi submenu ----------

def groups_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Global obuna o'rnatish", callback_data="grp_setglobalsub")
    builder.button(text="🗑 Global obunani bekor qilish", callback_data="grp_removeglobalsub")
    builder.button(text="📢 Guruhlarga xabar yuborish (bir martalik)", callback_data="grp_broadcast")
    builder.button(text="⏰ Avtomatik takroriy reklama", callback_data="menu_scheduled")
    builder.button(text="⬅️ Bosh menyu", callback_data="admin_back_main")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Avtomatik takroriy reklama submenu ----------

def scheduled_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi qo'shish", callback_data="sched_add")
    builder.button(text="📃 Ro'yxat / o'chirish", callback_data="sched_list")
    builder.button(text="⬅️ Orqaga", callback_data="menu_groups")
    builder.adjust(1)
    return builder.as_markup()


def scheduled_target_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Faqat guruhlarga", callback_data="sched_target_groups")
    builder.button(text="👤 Faqat foydalanuvchilarga", callback_data="sched_target_users")
    builder.button(text="🌐 Ikkalasiga ham", callback_data="sched_target_both")
    builder.adjust(1)
    return builder.as_markup()


def scheduled_remove_keyboard(ads):
    builder = InlineKeyboardBuilder()
    for ad in ads:
        status = "✅" if ad["enabled"] else "⏸"
        target_label = {"groups": "guruhlar", "users": "foydalanuvchilar", "both": "hammaga"}.get(ad["target"], ad["target"])
        builder.button(
            text=f"{status} {ad['send_time']} — {target_label} 🗑",
            callback_data=f"sched_remove_{ad['id']}"
        )
    builder.button(text="⬅️ Orqaga", callback_data="menu_scheduled")
    builder.adjust(1)
    return builder.as_markup()