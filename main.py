import logging
from bot import create_bot
from web import create_app

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    create_app()
    create_bot()
