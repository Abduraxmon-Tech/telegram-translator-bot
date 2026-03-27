import telebot
from telebot import types
from words import word_list

# Bot tokeni
bot = telebot.TeleBot('7928658663:AAHIFCzzL-2qjkZJwxvoVQ0TQtXqsr3XRr0')

# Global o'zgaruvchilar
user_states = {}  # Faylga saqlash mexanizmi qo‘shish kerak

# Yordamchi funksiya - Admin klaviaturasi yaratish
def create_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("So'z qo'shish", "So'z o'chirish", "Chiqish")
    return keyboard

# Admin panelga kirish
@bot.message_handler(func=lambda message: message.text == "AAABBB2025")
def enter_admin_panel(message):
    user_states[message.chat.id] = "admin"
    bot.send_message(
        message.chat.id, 
        "Admin paneliga xush kelibsiz!", 
        reply_markup=create_admin_keyboard()
    )

# Admin panel tugmalarini boshqarish
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "admin")

def handle_admin_panel(bot, message, user_states):
    if message.text == "So'z qo'shish":
        msg = bot.send_message(message.chat.id, "Har bir so'zni yangi qatordan yozing! (masalan: kitob - book):")
        bot.register_next_step_handler(msg, lambda msg:process_add_words(bot, msg))
    elif message.text == "So'z o'chirish":
        word_names = [f"{w['uz']} - {w['en']}" for w in word_list]
        if word_names:
            msg = bot.send_message(message.chat.id, f"\n".join([f"{i + 1}. {word['uz']} - {word['en']}" for i, word in enumerate(word_list)]) + "\n___________________\n❌O'chirish uchun so'zni id kiriting\n☝️Hoslasangiz 1 ta id\n🤷‍♂️Hohlasangiz (1-10)oraliqni kiriting:")
            bot.register_next_step_handler(msg, lambda msg: process_delete_word(bot, msg))
        else:
            bot.send_message(message.chat.id, "🤷‍♂Hech qanday so'z mavjud emas!")
    elif message.text == "Chiqish":
        user_states[message.chat.id] = "default"
        bot.send_message(message.chat.id, "🚪Admin paneldan chiqdingiz.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "❓Noma'lum buyruq. Iltimos, tugmalardan foydalaning.")

def process_add_words(bot, message):
    words_input = message.text.strip()
    words = words_input.split('\n')  # Har bir yangi so'z yangi qatorda yoziladi
    added_words = []
    errors = []

    for word_input in words:
        try:
            uz_word, en_word = word_input.split(' - ')  # 'so'z - tarjima' formatida bo'lishi kerak
            word_list.append({"uz": uz_word, "en": en_word})
            added_words.append(f"{uz_word} - {en_word}")
        except ValueError:
            errors.append(word_input)

    if added_words:
        bot.send_message(message.chat.id, f"✅So'zlar muvaffaqiyatli qo'shildi.")
    if errors:
        bot.send_message(message.chat.id, f"🧐Quyidagi so'z(lar) noto'g'ri formatda kiritilgan:\n" + "\n".join(errors) + "\nIltimos, quyidagi formatda yuboring: so'z - tarjima")

def process_delete_word(bot, message):
    # Kiruvchi matnni tozalash va index yoki index oralig'ini olish
    input_text = message.text.strip()

    try:
        # Agar index oraligi bo'lsa, uni qayta ishlash
        if '-' in input_text:
            start_index, end_index = map(int, input_text.split('-'))
            indices_to_delete = range(start_index - 1, end_index)  # Foydalanuvchiga 1 dan boshlab ko'rsatiladi
        else:
            # Agar faqat bitta index berilgan bo'lsa
            indices_to_delete = [int(input_text) - 1]

        deleted_words = []

        for index in sorted(indices_to_delete, reverse=True):  # Teskari tartibda o'chirish uchun
            if 0 <= index < len(word_list):
                deleted_word = word_list.pop(index)
                deleted_words.append(f"{index + 1} - {deleted_word['uz']} - {deleted_word['en']}")

        if deleted_words:
            bot.send_message(message.chat.id, f"✅O'chirish muvaffaqiyatli bo'ldi.")
        else:
            bot.send_message(message.chat.id, "Ko'rsatilgan index(lar)ga mos so'z topilmadi.")

    except ValueError:
        bot.send_message(message.chat.id, "❗️Noto'g'ri format! Iltimos, to'g'ri index yoki index oralig'ini kiriting. Masalan: 1 yoki 1-10")

def list_words_with_indices(bot, message):
    if word_list:
        response = "So'zlar ro'yxati:\n"
        response += "\n".join([f"{i + 1} - {word['uz']} - {word['en']}" for i, word in enumerate(word_list)])
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "😳So'zlar ro'yxati bo'sh.")
