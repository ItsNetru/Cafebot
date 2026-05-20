import telebot
import json
import os
import django
import sys
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- DJANGO SETUP ----------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cafe_app1'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafe_app1.settings")
django.setup()

from app.models import Order

# ---------- BOT CONFIGURATION ----------
TOKEN = os.getenv("BOT_TOKEN", "8668039978:AAFZbuPzfqjlVX-PP0WazywAQXS4nUtmpR8")
bot = telebot.TeleBot(TOKEN)

# ---------- IN-MEMORY STORAGE ----------
user_baskets = {}
user_states = {}

# ---------- MENU DATA ----------
menu = {
    "Burger": 2000,
    "Pizza": 3000,
    "Cola": 800,
    "Fries": 1200
}


# ---------- SAFE UI UPDATES (ANTI-400 ERROR & ANTI-LOADING BARS) ----------
def safe_edit_text(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown", call_id=None):
    if call_id:
        try:
            bot.answer_callback_query(call_id)
        except:
            pass

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in e.description:
            pass
        else:
            try:
                bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            except:
                pass


# ---------- INTERFACE MARKUPS ----------
def main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Menu", callback_data="menu"),
        InlineKeyboardButton("🛒 Cart", callback_data="cart")
    )
    markup.add(
        InlineKeyboardButton("🧾 My Orders", callback_data="orders"),
        InlineKeyboardButton("ℹ️ About Us", callback_data="info")
    )
    markup.add(InlineKeyboardButton("❓ Help", callback_data="help"))
    return markup


def menu_markup():
    markup = InlineKeyboardMarkup()
    for name, price in menu.items():
        markup.add(InlineKeyboardButton(f"➕ {name} — {price}₸", callback_data=f"add_{name}"))
    markup.add(
        InlineKeyboardButton("🛒 Go to Cart", callback_data="cart"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="main")
    )
    return markup


def cart_markup(basket):
    markup = InlineKeyboardMarkup()
    for item in basket:
        markup.add(InlineKeyboardButton(f"❌ Remove {item}", callback_data=f"remove_{item}"))
    if basket:
        markup.add(InlineKeyboardButton("🗑 Clear Cart", callback_data="clear_cart"))
        markup.add(InlineKeyboardButton("📍 Place Order", callback_data="address"))
    markup.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main"))
    return markup


def cart_text(basket):
    if not basket:
        return "🛒 Your cart is empty."
    text = "🛒 Your Cart:\n\n"
    total = 0
    for item, qty in basket.items():
        price = menu[item] * qty
        total += price
        text += f"  • {item} x{qty} = {price}₸\n"
    text += f"\n💰 Total: {total}₸"
    return text



# INDEPENDENT REQUEST HANDLERS
# =====================================================================

# Command /start
@bot.message_handler(commands=['start'])
def command_start(message):
    user_baskets[message.from_user.id] = user_baskets.get(message.from_user.id, {})
    bot.send_message(
        message.chat.id,
        "☕ Welcome to our Cafe! Please select an option below:",
        reply_markup=main_menu_markup()
    )


# Command /help
@bot.message_handler(commands=['help'])
def command_help(message):
    text = (
        "❓ **Bot Commands Help:**\n\n"
        "/start — Restart the bot and open main menu\n"
        "/help — Show this help message\n"
        "/info — View cafe address and working hours\n\n"
        "You can also use the inline buttons to navigate."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_markup())


# Command /info
@bot.message_handler(commands=['info'])
def command_info(message):
    text = (
        "🏢 **About Our Cafe:**\n\n"
        "📍 Address: 123 Shevchenko St, Almaty\n"
        "🕒 Working Hours: 09:00 AM - 10:00 PM\n"
        "📞 Phone: +7 (777) 777-77-77\n\n"
        "Fast delivery of hot food right to your door!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_markup())


# Inline Navigation - Main Menu
@bot.callback_query_handler(func=lambda call: call.data == "main")
def callback_main_menu(call):
    safe_edit_text(
        call.message.chat.id,
        call.message.message_id,
        "☕ Cafe Main Menu:",
        reply_markup=main_menu_markup(),
        call_id=call.id
    )


# Inline Navigation - Food Menu
@bot.callback_query_handler(func=lambda call: call.data == "menu")
def callback_menu_view(call):
    safe_edit_text(
        call.message.chat.id,
        call.message.message_id,
        "🍽 Choose items from our menu:",
        reply_markup=menu_markup(),
        call_id=call.id
    )


# Inline Navigation - About Info
@bot.callback_query_handler(func=lambda call: call.data == "info")
def callback_info_view(call):
    text = (
        "🏢 **About Our Cafe:**\n\n"
        "📍 Address: 123 Shevchenko St, Almaty\n"
        "🕒 Working Hours: 09:00 AM - 10:00 PM\n\n"
        "Made with love!"
    )
    safe_edit_text(call.message.chat.id, call.message.message_id, text, reply_markup=main_menu_markup(),
                   call_id=call.id)


# Inline Navigation - Help Support
@bot.callback_query_handler(func=lambda call: call.data == "help")
def callback_help_view(call):
    text = "❓ Use the menu buttons to navigate. If the bot gets stuck, type /start."
    safe_edit_text(call.message.chat.id, call.message.message_id, text, reply_markup=main_menu_markup(),
                   call_id=call.id)


# Cart Action - Add Item
@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def callback_cart_add(call):
    user_id = call.from_user.id
    item = call.data[4:]

    if user_id not in user_baskets:
        user_baskets[user_id] = {}

    user_baskets[user_id][item] = user_baskets[user_id].get(item, 0) + 1
    basket = user_baskets[user_id]
    total = sum(menu[i] * q for i, q in basket.items())

    safe_edit_text(
        call.message.chat.id,
        call.message.message_id,
        f"🍽 Choose items from our menu:\n\n✅ {item} added! Total in cart: {total}₸",
        reply_markup=menu_markup(),
        call_id=call.id
    )


# Cart Action - View Cart
@bot.callback_query_handler(func=lambda call: call.data == "cart")
def callback_cart_view(call):
    user_id = call.from_user.id
    basket = user_baskets.get(user_id, {})
    safe_edit_text(call.message.chat.id, call.message.message_id, cart_text(basket), reply_markup=cart_markup(basket),
                   call_id=call.id)


# Cart Action - Remove Item
@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_"))
def callback_cart_remove(call):
    user_id = call.from_user.id
    item = call.data[7:]

    if user_id in user_baskets and item in user_baskets[user_id]:
        if user_baskets[user_id][item] > 1:
            user_baskets[user_id][item] -= 1
        else:
            del user_baskets[user_id][item]

    basket = user_baskets.get(user_id, {})
    safe_edit_text(call.message.chat.id, call.message.message_id, cart_text(basket), reply_markup=cart_markup(basket),
                   call_id=call.id)


# Cart Action - Clear Cart
@bot.callback_query_handler(func=lambda call: call.data == "clear_cart")
def callback_cart_clear(call):
    user_id = call.from_user.id
    user_baskets[user_id] = {}
    safe_edit_text(call.message.chat.id, call.message.message_id, "🗑 Cart has been cleared.",
                   reply_markup=main_menu_markup(), call_id=call.id)


#  Order Checkout
@bot.callback_query_handler(func=lambda call: call.data == "address")
def callback_checkout_start(call):
    user_id = call.from_user.id
    basket = user_baskets.get(user_id, {})

    if not basket:
        bot.answer_callback_query(call.id, "Your cart is empty!")
        return

    user_states[user_id] = {
        "state": "waiting_address",
        "chat_id": call.message.chat.id,
        "message_id": call.message.message_id
    }

    safe_edit_text(
        call.message.chat.id,
        call.message.message_id,
        "📍 Please type your delivery address:",
        reply_markup=None,
        call_id=call.id
    )


#  View Order History (Django ORM)
@bot.callback_query_handler(func=lambda call: call.data == "orders")
def callback_orders_history(call):
    try:
        orders = Order.objects.filter(user_id=call.from_user.id).order_by('-id')[:5]
    except Exception as e:
        safe_edit_text(call.message.chat.id, call.message.message_id, f"❌ Error fetching data: {str(e)}",
                       reply_markup=main_menu_markup(), call_id=call.id)
        return

    if not orders:
        safe_edit_text(call.message.chat.id, call.message.message_id, "🧾 You have no orders yet.",
                       reply_markup=main_menu_markup(), call_id=call.id)
        return

    text = "🧾 **Your Recent Orders:**\n\n"
    for o in orders:
        items = json.loads(o.items)
        text += f"📦 **Order #{o.id}**\n"
        for i, q in items.items():
            text += f"  - {i} x{q}\n"
        text += f"💰 Total: {o.total}₸\n"
        text += f"📊 Status: {o.get_status_display()}\n"
        text += "─────────────\n"

    safe_edit_text(call.message.chat.id, call.message.message_id, text, reply_markup=main_menu_markup(),
                   call_id=call.id)


# =====================================================================
# TEXT PROCESSING
# =====================================================================

@bot.message_handler(func=lambda m: True)
def handle_text_and_errors(message):
    user_id = message.from_user.id
    state_data = user_states.get(user_id)

    if isinstance(state_data, dict) and state_data.get("state") == "waiting_address":
        address = message.text.strip()

        if len(address) < 5:
            bot.send_message(message.chat.id, "❌ Address is too short. Please enter a valid delivery address.")
            return

        user_states[user_id] = None
        basket = user_baskets.get(user_id, {})

        if not basket:
            bot.send_message(message.chat.id, "❌ Your cart is empty!", reply_markup=main_menu_markup())
            return

        total = sum(menu[i] * q for i, q in basket.items())
        items_text = "\n".join(f"  • {i} x{q}" for i, q in basket.items())

        try:
            order = Order.objects.create(
                user_id=user_id,
                username=message.from_user.username or "Customer",
                items=json.dumps(basket),
                total=total,
                address=address
            )
            user_baskets[user_id] = {}

            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass

            safe_edit_text(
                state_data["chat_id"],
                state_data["message_id"],
                f"✅ **Order #{order.id} placed successfully!**\n\n"
                f"📦 Items:\n{items_text}\n\n"
                f"💰 Total: {total}₸\n"
                f"📍 Address: {address}\n"
                f"📊 Status: Pending",
                reply_markup=main_menu_markup()
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Database error: {str(e)}", reply_markup=main_menu_markup())

    else:
        bot.reply_to(
            message,
            "🤖 I didn't understand that command or text.\n"
            "Please use the menu buttons or available commands: /start, /help.",
            reply_markup=main_menu_markup()
        )



if __name__ == '__main__':
    print("Bot is successfully running...")
    bot.infinity_polling()