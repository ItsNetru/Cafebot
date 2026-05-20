#  Cafe Telegram Bot

A food ordering Telegram bot built with Python, pyTelegramBotAPI, and Django. Users can browse a menu, add items to a cart, place orders with delivery address, and view their order history — all inside Telegram.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Main programming language |
| pyTelegramBotAPI | Telegram Bot interface and handlers |
| Django 5 | ORM, database models, Admin panel |
| SQLite | Persistent order storage |
| json | Serializing cart items for the database |

---

## 📁 Project Structure

```
project/
├── bot.py                  # Main bot file — all handlers and logic
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── cafe_app1/              # Django project
    ├── manage.py
    ├── db.sqlite3          # SQLite database (auto-created)
    ├── cafe_app1/          # Django settings, urls, wsgi
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── app/                # Django app
        ├── models.py       # Order model
        ├── admin.py        # Admin panel configuration
        └── migrations/     # Database migrations
```

---

##  Installation

**1. Clone or download the project:**
```bash
git clone <https://github.com/ItsNetru/Cafebot>
cd project
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Apply Django migrations:**
```bash
cd cafe_app1
python manage.py migrate
cd ..
```

**4. (Optional) Create a Django admin superuser:**
```bash
cd cafe_app1
python manage.py createsuperuser
cd ..
```

---

##  Running the Bot

```bash
python bot.py
```

The bot will start and print `Bot is successfully running...`

To open the **Django Admin panel** (manage orders, change statuses):
```bash
cd cafe_app1
python manage.py runserver
```
Then open: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

## 💬 Bot Commands

| Command | Description |
|---|---|
| `/start` | Open main menu |
| `/help` | Show available commands |
| `/info` | Cafe address and working hours |

---

##  Bot Features

- **Menu** — browse 4 food items with prices
- **Add to cart** — add items, see running total instantly
- **Cart** — view cart, remove individual items or clear all
- **Place Order** — enter delivery address and confirm
- **My Orders** — view last 5 orders with status
- **About Us** — cafe info
- **Help** — usage instructions
- **Error handling** — empty cart, short address, unknown commands, database errors

---

## 📊 Order Status Flow

Orders are saved to SQLite and managed through Django Admin:

`Pending` → `Cooking` → `Delivering` → `Done`

---


##  Author Danial Katkabaev

Final project for the discipline: **"Programming in Python"**
