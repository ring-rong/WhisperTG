import os

class Config:
    WHISPER_MIBOT_TOKEN = os.environ.get("WHISPER_MIBOT_TOKEN") or "bot_token"
