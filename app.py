import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Filter
from aiogram import F
from gradio_client import Client
from tempfile import NamedTemporaryFile
from moviepy.editor import VideoFileClip

class NonMediaFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return not message.voice and not message.audio and not message.video

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
    await message.reply("Бот для получения текста из аудио и видео")

@dp.message(NonMediaFilter())
async def get_text(message: types.Message):
    await message.reply(f"Не понимаю: {message.text}\nНаберите команду `/help` для справки")

@dp.message(F.voice)
@dp.message(F.audio)
async def get_audio(message: types.Message):
    voice_object = message.voice or message.audio
    with NamedTemporaryFile(delete=False) as temp_file:
        voice_file_path = temp_file.name
        await bot.download(voice_object.file_id, destination=voice_file_path)
        print(f"Audio file downloaded: {voice_file_path}")
        await process_audio(message, voice_file_path)

@dp.message(F.video)
async def get_video(message: types.Message):
    video_object = message.video
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        video_file_path = temp_file.name
        await bot.download(video_object.file_id, destination=video_file_path)
        print(f"Video file downloaded: {video_file_path}")
        
        with NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
            audio_file_path = audio_file.name
            video = VideoFileClip(video_file_path)
            video.audio.write_audiofile(audio_file_path)
            video.close()
            await process_audio(message, audio_file_path)
        
        os.remove(video_file_path)

async def process_audio(message: types.Message, audio_file_path: str):
    mess = await message.reply("Processing audio to text...")
    try:
        print("Sending request to Whisper API...")
        result = whisper_api_client.predict(
            audio_file_path,
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
        os.remove(audio_file_path)  # Remove the downloaded file
    
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
