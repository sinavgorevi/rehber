import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Bot token'ını çevre değişkeninden al
TOKEN = os.environ.get("BOT_TOKEN")

# Updater'ı oluştururken bu token'ı kullanın
updater = Updater(TOKEN, use_context=True)

# Bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"
FILE_PATH_TXT = "file_path.txt"
USERS_FILE = "users.txt"

def save_file_path(file_path: str) -> None:
    with open(FILE_PATH_TXT, "w") as f:
        f.write(file_path)

def load_file_path() -> str:
    if os.path.exists(FILE_PATH_TXT):
        with open(FILE_PATH_TXT, "r") as f:
            return f.read().strip()
    return ""

def is_user_authorized(user_id: int) -> bool:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            authorized_users = f.read().splitlines()
            return str(user_id) in authorized_users
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text("Bu botu kullanamazsınız.")
        return

    await update.message.reply_text("Bot'a hoş geldiniz! Lütfen bir Excel dosyası yükleyin ve sorgulamak istediğiniz kurum kodunu girin.")

async def dosya_al(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text("Bu botu kullanamazsınız.")
        return

    document = update.message.document
    if not document or not document.file_name.endswith('.xlsx'):
        await update.message.reply_text("Lütfen geçerli bir Excel dosyası yükleyin.")
        return

    file = await document.get_file()
    file_path = os.path.join(os.getcwd(), document.file_name)
    await file.download_to_drive(file_path)

    save_file_path(file_path)
    await update.message.reply_text(f"Dosya başarıyla yüklendi: {document.file_name}")

async def kurum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text("Bu botu kullanamazsınız.")
        return

    if not context.args:
        await update.message.reply_text("Lütfen bir kurum kodu veya anahtar kelime girin.")
        return

    anahtar_kelime = context.args[0].lower()
    file_path = load_file_path()

    if not file_path:
        await update.message.reply_text("Önce bir dosya yükleyin.")
        return

    try:
        df = pd.read_excel(file_path, sheet_name='kurum')

        # Sütun adını index ile bul
        b_column_index = 1  # "B" sütunu Excel'de 1. index'e denk gelir
        if b_column_index >= len(df.columns):
            await update.message.reply_text("Excel dosyasında 'B' sütunu bulunamadı.")
            return

        # Sadece "B" sütununda anahtar kelimeyi ara
        mask = df.iloc[:, b_column_index].astype(str).str.lower().str.contains(anahtar_kelime)
        result = df[mask]

        if result.empty:
            await update.message.reply_text("Bu anahtar kelimeye ait bilgi bulunamadı.")
        else:
            for _, row in result.iterrows():
                mesaj = "\n".join([f"{df.columns[col_index]}: {row[col_index]}" for col_index in range(len(df.columns))])
                await update.message.reply_text(mesaj)

            if len(result) > 1:
                await update.message.reply_text(f"Toplam {len(result)} sonuç bulundu.")
    except Exception as e:
        await update.message.reply_text(f"Hata oluştu: {str(e)}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("kurum", kurum))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_al))

    # run_polling async methodunu doğrudan çağırın
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
