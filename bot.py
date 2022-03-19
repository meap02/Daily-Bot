# bot.py

import os
import discord
from yaml import load, dump
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_settings():
    full_file_path = Path(__file__).parent.joinpath('login.yaml')
    with open("login.yaml") as f:
        f = load(f, Loader=yaml.Loader)
    return f


Token = os.getenv()
