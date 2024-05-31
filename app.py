import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from config import Config
from gradio_client import Client

# Initialize bot
bot = Bot(token=Config.WHISPER_MIBOT_TOKEN)
dp = Dispatcher()
print("bot started")

# Initialize Whisper API client
whisper_api_client = Client("https://openai-whisper.hf.space/")

# Command handlers
@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.answer(f"start command. Chat id: {message.chat.id}")

@dp.message(Command("id"))
async def command_id(message: types.Message):
    await message.reply(f"chat id: {message.chat.id}\nuser_id: {message.from_user.id}")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.reply("Бот для получения текста из аудио")

@dp.message(F.text)
async def get_text(message: types.Message):
    await message.reply(f"Не понимаю: {message.text}\nНаберите команду `/help` для справки")

@dp.message(F.voice)
@dp.message(F.audio)
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

async def send_long_message(message: types.Message, text: str, max_symbols: int = 4000):
    if len(text) < max_symbols:
        await message.reply(text or "-")
    else:
        for i in range(0, len(text), max_symbols):
            t = text[i : i + 4000]
            await message.answer(text=t)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
