import asyncio
import os
import pathlib
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from db.utils import register_message, send_long_message
from config import Config
from gradio_client import Client

# Initialize bot
bot = Bot(token=Config.WHISPER_MIBOT_TOKEN)
dp = Dispatcher()

print("bot started")

# Delete existing webhook
response = requests.get(f"https://api.telegram.org/bot{Config.WHISPER_MIBOT_TOKEN}/deleteWebhook")
if response.status_code == 200:
    print("Webhook deleted successfully.")
else:
    print("Failed to delete webhook.")

# Initialize Whisper API client
whisper_api_client = Client("https://openai-whisper.hf.space/")

# Command handlers
@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.answer(f"start command. Chat id: {message.chat.id}")

@dp.message(Command("id"))
@register_message
async def command_id(message: types.Message):
    await message.reply(f"chat id: {message.chat.id}\nuser_id: {message.from_user.id}")

@dp.message(Command("help"))
@register_message
async def help_command(message: types.Message):
    await message.reply("Бот для получения текста из аудио")

@dp.message(F.text)
@register_message
async def get_text(message: types.Message):
    await message.reply(f"Не понимаю: {message.text}\nНаберите команду `/help` для справки")

@dp.message(F.voice)
@dp.message(F.audio)
@register_message
async def get_audio(message: types.Message):
    voice_object = message.voice or message.audio
    voice_file_path = await bot.download(voice_object)

    mess = await message.reply("Processing audio to text...")
    try:
        result = whisper_api_client.predict(
            voice_file_path,
            "transcribe",
            api_name="/predict"
        )
        text = result[0]
    except Exception as E:
        await message.reply("Error: Cannot extract text.")
        raise E
    finally:
        await mess.delete()
        os.remove(voice_file_path)  # Remove the downloaded file

    await send_long_message(message, text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
