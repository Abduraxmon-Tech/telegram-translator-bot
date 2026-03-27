import telebot
import json
import random
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from words import word_list
from admin import create_admin_keyboard, handle_admin_panel

# Bot tokenini kiriting
TOKEN = "7928658663:AAFcwk3B2ES508Z7JhosOjQFh_xvCEGo8qQ"
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi ma'lumotlari fayli
USERS_FILE = "users.json"

# Foydalanuvchi ma'lumotlarini yuklash
def load_users():
    try:
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Foydalanuvchi ma'lumotlarini saqlash
def save_users(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=4)

# Global foydalanuvchi ma'lumotlari
users = load_users()

#####################################################################################
@bot.message_handler(commands=['bot_info'])
def bot_info(message):
    info_text = (
        "ℹ️Bot haqida qisqacha.\n"
        "——————————————-\n"
        "🤖Bu botda \"Uzbekcha -> Inglizcha\" yoki \"Inglizcha -> Uzbekcha\" testlar topshirish orqali bilimingizni sinashingiz mumkin.\n"
        "🤞Botda 2 ta usulda te stni boshlash mumkin (UZ-EN yoki EN-UZ).\n"
        "✅Har bir yo'nalishda to'plangan ballar alohida hisoblanadi.\n"
        "———————————————\n"
        "📊ALL Reyting esa ikkala natijalarni yig'indisi hisoblanib Top 10 talikni aniqlaydi.\n\n"
        "🖼UZ-EN yoki EN-UZ yo'nalishidagi har bir to'g'ri javob uchun   \n🎉+1 bal qo'shiladi, xato javob uchun ayrilmaydi.\n\n"
        "🌟Stars ballari:\n"
        "⚠️Diqqat hushyor bo'ling bu ballar o'zgaruvchandir.\n"
        "✅Har bir tog'ri javob uchun 0.1 bal beriladi.\n"
        "❌Xato javob uchun -0.1 bal ayriladi (ikkala yo'nalishda ham).\n\n"
        "@savol_javob2_bot"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    start_button = telebot.types.InlineKeyboardButton("🏃‍♂️‍➡️ Testni boshlash", callback_data="restart:quiz")
    markup.add(start_button)
    bot.send_message(message.chat.id, info_text, reply_markup=markup)
    
@bot.message_handler(commands=["reyting"])
def show_rating_buttons(message):
    # Reyting tugmalarini yaratish
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔄 Testni qaytadan boshlash", callback_data="restart:quiz")
    )
    keyboard.add(
        InlineKeyboardButton("✨ ALL Reyting", callback_data="rating:all"),
        InlineKeyboardButton("🇺🇿 UZ-EN Reyting", callback_data="rating:uz_en"),
        InlineKeyboardButton("🇬🇧 EN-UZ Reyting", callback_data="rating:en_uz"),
        InlineKeyboardButton("🌟 Stars", callback_data="rating:stars")
    )

    # Xabarni o'zimiz yozamiz
    bot.send_message(
        chat_id=message.chat.id,
        text="Mana reytinglar:",
        reply_markup=keyboard
    )
#####################################################################################

# Start xabari
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        # Yangi foydalanuvchi qo'shish
        users[user_id] = {
            "id": message.from_user.id,
            "name": message.from_user.first_name,
            "username": message.from_user.username,
            "gender": None,  # Erkak yoki ayol kiritiladi
            "admin": False,  # Admin flagi
            "pointsUZ_EN": 0,  # Default qiymat 0
            "pointsEN_UZ": 0,   # Default qiymat 0
            "all_points": 0,  # Default qiymat 0
            "stars": 0.0  # Default qiymat 0.0
        }
        save_users(users)
        # Genderni so'rash
        bot.send_message(
            message.chat.id,
            "🙂Assalomu alaykum! Jinsingizni tanlang:",
            reply_markup=gender_inline_keyboard()
        )
    elif users[user_id]["gender"] is None:
        bot.send_message(
            message.chat.id,
            "Iltimos, avval jinsingizni tanlang:",
            reply_markup=gender_inline_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"😇Xush kelibsiz, {users[user_id]['name']}! Qaytib kelganingizdan xursandmiz."
        )
        show_inline_main_menu(message)

# Gender inline tugmachalari
def gender_inline_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Erkak", callback_data="gender_Erkak"),
        InlineKeyboardButton("Ayol", callback_data="gender_Ayol")
    )
    return markup

# Genderni qayta ishlash
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    user_id = str(call.from_user.id)
    if user_id in users:
        selected_gender = call.data.split("_")[1]
        users[user_id]["gender"] = selected_gender
        save_users(users)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🙆‍♂️Rahmat! Jinsingiz: {selected_gender}."
        )
        show_inline_main_menu(call.message)
    else:
        bot.send_message(
            call.message.chat.id,
            "Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring."
        )
# Foydalanuvchi jinsini tekshirish
def check_gender(message):
    user_id = str(message.from_user.id)
    if user_id not in users or users[user_id].get("gender") is None:
        bot.send_message(
            message.chat.id,
            "❗️Iltimos, avval jinsingizni tanlang!",
            reply_markup=gender_inline_keyboard()
        )
        return False
    return True


# Foydalanuvchi holatini saqlash uchun lug'at
user_states = {}

# Admin paneliga kirish
@bot.message_handler(func=lambda message: message.text == "AAABBB2025")
def enter_admin_panel(message):
    user_states[message.chat.id] = "admin"
    admin_keyboard = create_admin_keyboard()
    bot.send_message(message.chat.id, "Admin paneliga xush kelibsiz!", reply_markup=admin_keyboard)

# Barcha xabarlarni qayta ishlash
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_state = user_states.get(message.chat.id, "default")
    
    if user_state == "admin":
        # Admin panelidagi xabarlarni admin.py ga yo'naltirish
        handle_admin_panel(bot, message, user_states)
    else:
        # Oddiy foydalanuvchi uchun javob
        show_inline_main_menu(message)
        
# Global dictionaries for user sessions
user_sessions = {}

@bot.callback_query_handler(func=lambda call: call.data == "restart:quiz")
def restart_quiz(call):
    show_inline_main_menu(call.message)

# Asosiy menyuni yaratish funksiyasi
def show_inline_main_menu(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🇺🇿UZ-EN", callback_data="start:🇺🇿UZ-EN"),
        InlineKeyboardButton("🇬🇧EN-UZ", callback_data="start:🇬🇧EN-UZ")
    )
    bot.send_message(
        message.chat.id,
        "\u2753 Qaysi usulda savol-javob qilishni xohlaysiz?",
        reply_markup=keyboard
    )

def start_quiz(message, quiz_type, num_questions):
    user_id = message.chat.id
    questions = random.sample(word_list, num_questions)
    user_sessions[user_id] = {
        "quiz_type": quiz_type,
        "questions": questions,
        "current_index": 0,
        "correct": 0,
        "incorrect": 0,
        "answered": [None] * num_questions,
        "answers": [None] * num_questions,
        "message_id": None
    }
    send_question(message, user_id)
    
def set_question_count(message, quiz_type):
    try:
        num_questions = int(message.text)
        if num_questions < 5 or num_questions > len(word_list):
            raise ValueError
        start_quiz(message, quiz_type, num_questions)
    except ValueError:
        bot.send_message(
            message.chat.id,
            f"Noto'g'ri son kiritildi. Iltimos, sonni qayta kiriting (min: 5, max: {len(word_list)}):"
        )
        bot.register_next_step_handler(
            message, lambda msg: set_question_count(msg, quiz_type)
        )    
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("start"))
def choose_quiz_type(call):
    quiz_type = call.data.split(":")[1]
    bot.send_message(
        call.message.chat.id,
        f"Test savollar sonini kiriting (min: 5, max: {len(word_list)}):"
    )
    bot.register_next_step_handler(
        call.message, lambda message: set_question_count(message, quiz_type)
    )

def send_question(message, user_id):
    session = user_sessions[user_id]
    index = session["current_index"]
    question = session["questions"][index]
    quiz_type = session["quiz_type"]

    question_text = question["uz"] if quiz_type == "🇺🇿UZ-EN" else question["en"]
    correct_answer = question["en"] if quiz_type == "🇺🇿UZ-EN" else question["uz"]

    # Javoblar tartibini saqlash
    if "options_order" not in session:
        session["options_order"] = {}

    if index not in session["options_order"]:
        # Javoblar faqat birinchi marta random qilinadi
        options = [correct_answer] + random.sample(
            [q["en"] if quiz_type == "🇺🇿UZ-EN" else q["uz"] for q in word_list if q != question], 3
        )
        random.shuffle(options)
        session["options_order"][index] = options
    else:
        # Avvalgi tartibni qayta yuklash
        options = session["options_order"][index]

    keyboard = InlineKeyboardMarkup()
    for i, option in enumerate(options):
        # Tugmalar matnini tayyorlash
        if session["answered"][index] is not None:
            is_correct_option = option == correct_answer
            if session["answers"][index] == option:
                # Javob foydalanuvchi tanlagan javobga mos kelsa, stiker qo‘shiladi
                button_text = f"✅ {option}" if session["answered"][index] else f"❌ {option}"
            elif is_correct_option:
                # To‘g‘ri javob stiker bilan belgilanadi
                button_text = f"✅ {option}"
            else:
                # Oddiy tugma matni
                button_text = option
        else:
            # Javob berilmagan holatda oddiy tugma
            button_text = option

        callback_data = f"answer:{index}:{i}:{option == correct_answer}"
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )
        keyboard.add(button)

    # Navigatsiya tugmalarini qo‘shish
    if index == len(session["questions"]) - 1:
        keyboard.add(
            InlineKeyboardButton("\u2b05\ufe0f Orqaga", callback_data="navigate:back"),
            InlineKeyboardButton("\ud83d\udcca Natijalar", callback_data="navigate:results")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("\u2b05\ufe0f Orqaga", callback_data="navigate:back"),
            InlineKeyboardButton("\u27a1\ufe0f Keyingi", callback_data="navigate:next")
        )

    # Xabar matni
    text = f"\u2753 {index + 1}-Savol:\n\n🧐 {question_text} - ?"
    if session["answered"][index] is not None:
        if session["answered"][index]:
            text += "\n\n✅ To'g'ri javob bergansiz!"
        else:
            text += "\n\n❌ Noto'g'ri javob bergansiz!"

    # Xabarni tahrirlash yoki yangi xabar yuborish
    if session.get("message_id"):
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=session["message_id"],
                text=text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Xabarni qayta tahrirlashda xatolik: {e}")
            sent_message = bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )
            session["message_id"] = sent_message.message_id
    else:
        sent_message = bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        session["message_id"] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer"))
def handle_answer(call):
    user_id = call.message.chat.id
    session = user_sessions[user_id]
    _, index, chosen_idx, is_correct = call.data.split(":")
    index, chosen_idx = int(index), int(chosen_idx)
    is_correct = is_correct == "True"

    if session["answered"][index] is not None:
        bot.answer_callback_query(call.id, "Bu savolga javob berdingiz!")
        return

    session["answered"][index] = is_correct
    session["answers"][index] = call.message.reply_markup.keyboard[chosen_idx][0].text

    # Javob to'g'rimi yoki noto'g'ri ekanligini tekshirish
    update_user_points(user_id, session["quiz_type"], is_correct)

    if is_correct:
        session["correct"] += 1
    else:
        session["incorrect"] += 1

    # Javob belgilari (✅ yoki ❌) ni tiklash
    keyboard = call.message.reply_markup
    for i, button_row in enumerate(keyboard.keyboard):
        button = button_row[0]
        if session["answered"][index] is not None:  # Agar javob allaqachon berilgan bo'lsa
            if i == chosen_idx:
                button.text = f"✅ {button.text.strip('✅ ❌')}" if is_correct else f"❌ {button.text.strip('✅ ❌')}"
            elif button.text.strip("✅ ❌") == session["questions"][index]["en" if session["quiz_type"] == "🇺🇿UZ-EN" else "uz"]:
                button.text = f"✅ {button.text.strip('✅ ❌')} "
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print(f"Xabarni qayta tahrirlashda xatolik: {e}")
        
def update_user_points(user_id, quiz_type, is_correct):
    try:
        with open("users.json", "r") as f:
            users_data = json.load(f)
    except FileNotFoundError:
        users_data = {}

    if str(user_id) not in users_data:
        users_data[str(user_id)] = {"pointsUZ_EN": 0, "pointsEN_UZ": 0, "stars": 0.0}

    user_data = users_data[str(user_id)]
    
    # ballarni tanlovga qarab belgilanadi
    points_key = "pointsUZ_EN" if quiz_type == "🇺🇿UZ-EN" else "pointsEN_UZ"
    
    if is_correct:
        user_data[points_key] += 1  # Ballarni qo'shish
        user_data["stars"] += 0.1  # Yulduz ballarini qo'shish
    else:
        user_data["stars"] -= 0.1  # Noto'g'ri javobda yulduz ballarini kamaytirish

    # Foydalanuvchi ma'lumotlarini qayta saqlash
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)

@bot.callback_query_handler(func=lambda call: call.data.startswith("navigate"))
def handle_navigation(call):
    user_id = call.message.chat.id
    session = user_sessions[user_id]
    action = call.data.split(":")[1]

    if action == "back":
        if session["current_index"] > 0:
            session["current_index"] -= 1
            send_question(call.message, user_id)
        else:
            bot.answer_callback_query(call.id, "Orqaga qaytish imkoni yo'q!")
    elif action == "next":
        if session["current_index"] < len(session["questions"]) - 1:
            session["current_index"] += 1
            send_question(call.message, user_id)
        else:
            show_results(call.message, user_id)
    elif action == "results":
        show_results(call.message, user_id)

def show_results(message, user_id):
    session = user_sessions[user_id]

    total = len(session["questions"])
    correct = session["correct"]
    incorrect = session["incorrect"]
    percentage = (correct / total) * 100

    result_message = (
        f"✅ To'g'ri javoblar: {correct}\n"
        f"❌ Noto'g'ri javoblar: {incorrect}\n"
        f"📊 Umumiy natija: {percentage:.2f}%\n\n"
    )

    if percentage <= 25:
        result_message += "Telefonni kamroq o'ynab, ko'proq dars qilishingiz kerak. 📚"
    elif percentage <= 50:
        result_message += "Dangasalik qilmang, yaxshiroq o'qing! 📘"
    elif percentage <= 75:
        result_message += "Yaxshi natija, lekin baribir zo'r emas. 😊"
    else:
        result_message += "Zo'r, o'qisa bo'larkanuu! 🥳"

    # Reyting tugmalarini yaratish
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔄 Testni qaytadan boshlash", callback_data="restart:quiz")
    )
    keyboard.add(
        InlineKeyboardButton("✨ ALL Reyting", callback_data="rating:all"),
        InlineKeyboardButton("🇺🇿 UZ-EN Reyting", callback_data="rating:uz_en"),
        InlineKeyboardButton("🇬🇧 EN-UZ Reyting", callback_data="rating:en_uz"),
        InlineKeyboardButton("🌟 Stars", callback_data="rating:stars")
    )

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=session["message_id"],
            text=result_message,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Natijalarni chiqarishda xatolik: {e}")
        session["message_id"] = bot.send_message(
            chat_id=message.chat.id,
            text=result_message,
            reply_markup=keyboard
        ).message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("rating"))
def show_rating(call):
    rating_type = call.data.split(":")[1]
    user_id = call.message.chat.id

    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)

        # Foydalanuvchilar ma'lumotlarini yig'ish
        if rating_type == "all":
            scores = [(u["name"], u["pointsUZ_EN"] + u["pointsEN_UZ"]) for u in users.values()]
            title = "✨ ALL Reyting (Umumiy ballar):"
        elif rating_type == "uz_en":
            scores = [(u["name"], u["pointsUZ_EN"]) for u in users.values()]
            title = "🇺🇿 UZ-EN Reyting:"
        elif rating_type == "en_uz":
            scores = [(u["name"], u["pointsEN_UZ"]) for u in users.values()]
            title = "🇬🇧 EN-UZ Reyting:"
        elif rating_type == "stars":
            # Foydalanuvchilarni username va rounded stars bilan olish
            scores = [(u["name"], round(u["stars"], 2)) for u in users.values()]
            title = "🌟 Stars Reyting:"

            # Reytingni saralash (yaxshiroq reyting yuqorida bo'ladi)
            scores = sorted(scores, key=lambda x: x[1], reverse=True)

            # Reyting xabarini yaratish
            if scores:
                message_text = f"{title}\n\n" + "\n".join(
                    [f"{idx + 1}. {username}: 💰{score}" for idx, (username, score) in enumerate(scores)]
                )
            else:
                message_text = f"{title}\n\nHech qanday foydalanuvchi reytingga ega emas."
        else:
            bot.answer_callback_query(call.id, "Xato: Reyting turi noto'g'ri.")
            return

        # Reytingni saralash va birinchi 10 foydalanuvchini olish
        top_scores = sorted(scores, key=lambda x: x[1], reverse=True)[:10]

        # Natijalarni tayyorlash
        rating_message = f"{title}\n\n"
        for i, (nickname, score) in enumerate(top_scores, start=1):
            rating_message += f"{i}. {nickname}: 💰{score}\n"

        # Xabarni tahrirlash
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=rating_message,
                reply_markup=call.message.reply_markup
            )
        except Exception as e:
            print(f"Reytingni tahrirlashda xatolik: {e}")
            bot.answer_callback_query(call.id, "Xabarni tahrirlashda xatolik yuz berdi.")
    except Exception as e:
        print(f"Reytingni ko'rsatishda xatolik: {e}")
        bot.answer_callback_query(call.id, "Reytingni ko'rsatishda xatolik yuz berdi.")

#--------------------------------------------------------------------------

# Botni doimiy ishga tushirish
if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    bot.infinity_polling()


