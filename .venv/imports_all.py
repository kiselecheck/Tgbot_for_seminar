from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup,
                           InlineKeyboardButton, KeyboardButtonPollType, WebAppInfo, BotCommand,
                           BotCommandScopeDefault, CallbackQuery, ReplyKeyboardRemove, TelegramObject)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.chat_action import ChatActionSender
import asyncio
import logging
import aiohttp
import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Any, Awaitable, Callable, Dict
from html import escape
from datetime import datetime, timedelta
import aiosqlite
import uuid
import json
import re