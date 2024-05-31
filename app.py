import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from gradio_client import Client
from tempfile import NamedTemporaryFile

WHISPER_MIBOT_TOKEN = os.getenv('WHISPER_MIBOT_TOKEN')
# Initialize bot
bot = Bot(token=WHISPER_MIBOT_TOKEN)
dp = Dispatcher()
print("Bot started")

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
    with NamedTemporaryFile(delete=False) as temp_file:
        voice_file_path = temp_file.name
        await voice_object.download(destination=voice_file_path)
        print(f"Audio file downloaded: {voice_file_path}")
        
        mess = await message.reply("Processing audio to text...")
        try:
            print("Sending request to Whisper API...")
            result = whisper_api_client.predict(
                voice_file_path,
                "transcribe",
                api_name="/predict"
            )
            print(f"Whisper API response: {result}")
            
            text = result
            if not text.strip():  # Проверка на пустой текст
                text = "Не удалось распознать речь в аудио"
        except Exception as E:
            print(f"Error: {str(E)}")
            await message.reply("Error: Cannot extract text.")
            raise E
        finally:
            await mess.delete()
            os.remove(voice_file_path)  # Remove the downloaded file
    
    await send_long_message(message, text)

async def send_long_message(message: types.Message, text: str, max_symbols: int = 4000):
    if not text.strip():  # Проверка на пустой текст
        await message.reply("Нет распознанного текста")
    elif len(text) < max_symbols:
        await message.reply(text)
    else:
        for i in range(0, len(text), max_symbols):
            t = text[i : i + 4000]
            await message.answer(text=t)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
