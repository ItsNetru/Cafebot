import telebot
import json
import os
import django
import sys



sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cafe_app1'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafe_app1.settings")
django.setup()

from app.models import Order

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8668039978:AAFZbuPzfqjlVX-PP0WazywAQXS4nUtmpR8"
bot = telebot.TeleBot(TOKEN)

user_baskets = {}
user_states = {}

menu = {
    "Burger": 2000,
    "Pizza": 3000,
    "Cola": 800,
    "Fries": 1200
}


def main_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 Menu", callback_data="menu"))
    markup.add(InlineKeyboardButton("🧾 My Orders", callback_data="orders"))
    return markup


def menu_markup():
    markup = InlineKeyboardMarkup()
    for name, price in menu.items():
        markup.add(InlineKeyboardButton(f"{name} — {price}₸", callback_data=f"add_{name}"))
    markup.add(InlineKeyboardButton("🛒 Cart", callback_data="cart"))
    markup.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main"))
    return markup


def cart_markup(basket):
    markup = InlineKeyboardMarkup()
    for item in basket:
        markup.add(InlineKeyboardButton(f"❌ Remove {item}", callback_data=f"remove_{item}"))
    markup.add(InlineKeyboardButton("📍 Enter address & Checkout", callback_data="address"))
    markup.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main"))
    return markup


def cart_text(basket):
    if not basket:
        return "🛒 Cart is empty"
    text = "🛒 Your Cart:\n\n"
    total = 0
    for item, qty in basket.items():
        price = menu[item] * qty
        total += price
        text += f"  {item} x{qty} = {price}₸\n"
    text += f"\n💰 Total: {total}₸"
    return text


# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "☕ Welcome to Cafe Bot!", reply_markup=main_menu_markup())


# ---------- MAIN MENU ----------
@bot.callback_query_handler(func=lambda call: call.data == "main")
def main_menu(call):
    bot.edit_message_text(
        "☕ Welcome to Cafe Bot!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu_markup()
    )


# ---------- MENU ----------
@bot.callback_query_handler(func=lambda call: call.data == "menu")
def menu_handler(call):
    bot.edit_message_text(
        "🍽 Choose your item:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=menu_markup()
    )


# ---------- ADD ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def add_item(call):
    user_id = call.from_user.id
    item = call.data[4:]

    if user_id not in user_baskets:
        user_baskets[user_id] = {}

    user_baskets[user_id][item] = user_baskets[user_id].get(item, 0) + 1

    # Обновляем то же сообщение с подтверждением
    basket = user_baskets[user_id]
    total = sum(menu[i] * q for i, q in basket.items())

    markup = menu_markup()

    bot.edit_message_text(
        f"🍽 Choose your item:\n\n✅ {item} added! Cart total: {total}₸",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ---------- CART ----------
@bot.callback_query_handler(func=lambda call: call.data == "cart")
def cart(call):
    user_id = call.from_user.id
    basket = user_baskets.get(user_id, {})

    text = cart_text(basket)
    markup = cart_markup(basket) if basket else main_menu_markup()

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ---------- REMOVE ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_"))
def remove_item(call):
    user_id = call.from_user.id
    item = call.data[7:]

    if item in user_baskets.get(user_id, {}):
        del user_baskets[user_id][item]

    basket = user_baskets.get(user_id, {})
    text = cart_text(basket)
    markup = cart_markup(basket) if basket else main_menu_markup()

    # Обновляем то же сообщение
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ---------- ADDRESS ----------
@bot.callback_query_handler(func=lambda call: call.data == "address")
def ask_address(call):
    user_id = call.from_user.id
    basket = user_baskets.get(user_id, {})

    if not basket:
        bot.answer_callback_query(call.id, "Cart is empty!")
        return

    user_states[user_id] = {
        "state": "waiting_address",
        "chat_id": call.message.chat.id,
        "message_id": call.message.message_id
    }

    bot.edit_message_text(
        "📍 Please enter your delivery address:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )


# ---------- TEXT (address) ----------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    state_data = user_states.get(user_id)

    if isinstance(state_data, dict) and state_data.get("state") == "waiting_address":
        user_states[user_id] = None
        address = message.text

        basket = user_baskets.get(user_id, {})
        if not basket:
            bot.send_message(message.chat.id, "❌ Cart is empty!", reply_markup=main_menu_markup())
            return

        total = sum(menu[i] * q for i, q in basket.items())
        items_text = "\n".join(f"  {i} x{q}" for i, q in basket.items())

        order = Order.objects.create(
            user_id=user_id,
            username=message.from_user.username or "unknown",
            items=json.dumps(basket),
            total=total,
            address=address
        )

        user_baskets[user_id] = {}

        # delete users message with address
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        # updating the same message instead of resending
        bot.edit_message_text(
            f"✅ Order #{order.id} placed!\n\n"
            f"📦 Items:\n{items_text}\n\n"
            f"💰 Total: {total}₸\n"
            f"📍 Address: {address}\n"
            f"📊 Status: {order.status}",
            state_data["chat_id"],
            state_data["message_id"],
            reply_markup=main_menu_markup()
        )


# ---------- ORDERS ----------
@bot.callback_query_handler(func=lambda call: call.data == "orders")
def my_orders(call):
    orders = Order.objects.filter(user_id=call.from_user.id).order_by('-id')

    if not orders:
        bot.edit_message_text(
            "🧾 You have no orders yet.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu_markup()
        )
        return

    text = "🧾 Your Orders:\n\n"
    for o in orders:
        items = json.loads(o.items)
        text += f"Order #{o.id}\n"
        for i, q in items.items():
            text += f"  - {i} x{q}\n"
        text += f"💰 Total: {o.total}₸\n"
        text += f"📊 Status: {o.status}\n"
        text += "─────────────\n"

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu_markup()
    )


bot.infinity_polling()