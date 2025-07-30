import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import re

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import pymongo
from pymongo import MongoClient
from bson import ObjectId

# Configuración desde variables de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN", "8063509725:AAFZIEmk0eNZ5Z56-HOz-bnwyg2rytPB-k")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1742433244"))
MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://zoobot:zoobot@zoolbot.6avd6qf.mongodb.net/zoolbot?retryWrites=true&w=majority&appName=Zoolbot")
DB_NAME = os.getenv("DB_NAME", "zoolbot")

# Configurar logging para producción
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Estados para FSM
class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_reward = State()
    waiting_url = State()

class UserManagementStates(StatesGroup):
    waiting_user_id = State()
    waiting_balance_change = State()

class AnnouncementStates(StatesGroup):
    waiting_message = State()

class MissionStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_reward = State()
    waiting_requirements = State()

# Inicializar bot y dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Conectar a MongoDB con manejo de errores mejorado
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    # Verificar conexión
    db.command('ping')
    logger.info("✅ Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to MongoDB: {e}")
    raise

class AdminBot:
    def __init__(self):
        self.maintenance_mode = False
        
    async def is_admin(self, user_id: int) -> bool:
        """Verificar si el usuario es administrador"""
        return user_id == ADMIN_ID
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener usuario por ID de Telegram"""
        try:
            return db.users.find_one({"telegram_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_all_users(self) -> List[Dict]:
        """Obtener todos los usuarios"""
        try:
            return list(db.users.find())
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de usuarios"""
        try:
            total_users = db.users.count_documents({})
            active_today = db.users.count_documents({
                "last_active": {"$gte": datetime.now().replace(hour=0, minute=0, second=0)}
            })
            banned_users = db.users.count_documents({"is_banned": True})
            total_diamonds = sum(user.get("diamonds", 0) for user in db.users.find())
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "banned_users": banned_users,
                "total_diamonds": total_diamonds
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                "total_users": 0,
                "active_today": 0,
                "banned_users": 0,
                "total_diamonds": 0
            }
    
    async def create_task(self, title: str, description: str, reward: int, url: str, verification_type: str = "url_visit") -> str:
        """Crear nueva tarea"""
        try:
            task = {
                "title": title,
                "description": description,
                "reward": reward,
                "url": url,
                "verification_type": verification_type,
                "is_active": True,
                "created_at": datetime.now()
            }
            result = db.tasks.insert_one(task)
            logger.info(f"Task created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    async def get_all_tasks(self) -> List[Dict]:
        """Obtener todas las tareas"""
        try:
            return list(db.tasks.find())
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    async def toggle_task_status(self, task_id: str) -> bool:
        """Activar/desactivar tarea"""
        try:
            task = db.tasks.find_one({"_id": ObjectId(task_id)})
            if task:
                new_status = not task.get("is_active", True)
                db.tasks.update_one(
                    {"_id": ObjectId(task_id)},
                    {"$set": {"is_active": new_status}}
                )
                return new_status
            return False
        except Exception as e:
            logger.error(f"Error toggling task status: {e}")
            return False
    
    async def update_user_balance(self, user_id: int, amount: int, operation: str = "add") -> bool:
        """Actualizar balance del usuario"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            if operation == "add":
                db.users.update_one(
                    {"telegram_id": user_id},
                    {"$inc": {"diamonds": amount}}
                )
            elif operation == "subtract":
                db.users.update_one(
                    {"telegram_id": user_id},
                    {"$inc": {"diamonds": -amount}}
                )
            elif operation == "set":
                db.users.update_one(
                    {"telegram_id": user_id},
                    {"$set": {"diamonds": amount}}
                )
            
            # Registrar transacción
            db.transactions.insert_one({
                "user_id": user_id,
                "type": "admin_adjustment",
                "amount": amount,
                "currency": "diamonds",
                "status": "completed",
                "created_at": datetime.now(),
                "operation": operation
            })
            
            return True
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            return False
    
    async def ban_user(self, user_id: int, reason: str = "") -> bool:
        """Banear usuario"""
        try:
            result = db.users.update_one(
                {"telegram_id": user_id},
                {"$set": {"is_banned": True, "ban_reason": reason, "banned_at": datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    async def unban_user(self, user_id: int) -> bool:
        """Desbanear usuario"""
        try:
            result = db.users.update_one(
                {"telegram_id": user_id},
                {"$set": {"is_banned": False}, "$unset": {"ban_reason": "", "banned_at": ""}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    async def send_announcement(self, message: str) -> Dict[str, int]:
        """Enviar anuncio a todos los usuarios"""
        users = await self.get_all_users()
        sent = 0
        failed = 0
        
        for user in users:
            if not user.get("is_banned", False):
                try:
                    await bot.send_message(user["telegram_id"], message)
                    sent += 1
                    await asyncio.sleep(0.05)  # Evitar rate limit
                except Exception as e:
                    logger.error(f"Error sending message to {user['telegram_id']}: {e}")
                    failed += 1
        
        return {"sent": sent, "failed": failed}

admin_bot = AdminBot()

# Keyboards
def get_main_keyboard():
    """Teclado principal del administrador"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Estadísticas", callback_data="stats"),
        InlineKeyboardButton(text="👥 Usuarios", callback_data="users_menu")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Tareas", callback_data="tasks_menu"),
        InlineKeyboardButton(text="🎯 Misiones", callback_data="missions_menu")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Anuncio", callback_data="announcement"),
        InlineKeyboardButton(text="💰 Transacciones", callback_data="transactions")
    )
    builder.row(
        InlineKeyboardButton(text="🔧 Mantenimiento", callback_data="maintenance"),
        InlineKeyboardButton(text="⚙️ Configuración", callback_data="settings")
    )
    return builder.as_markup()

def get_users_keyboard():
    """Teclado de gestión de usuarios"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Buscar Usuario", callback_data="search_user"),
        InlineKeyboardButton(text="📋 Lista Usuarios", callback_data="list_users")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Modificar Balance", callback_data="modify_balance"),
        InlineKeyboardButton(text="🚫 Ban/Unban", callback_data="ban_user")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="main_menu"))
    return builder.as_markup()

def get_tasks_keyboard():
    """Teclado de gestión de tareas"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Nueva Tarea", callback_data="new_task"),
        InlineKeyboardButton(text="📋 Ver Tareas", callback_data="list_tasks")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Activar/Desactivar", callback_data="toggle_task"),
        InlineKeyboardButton(text="🗑️ Eliminar Tarea", callback_data="delete_task")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="main_menu"))
    return builder.as_markup()

# Command handlers
@dp.message(Command(commands=['start', 'help']))
async def cmd_start(message: types.Message):
    """Comando de inicio"""
    if not await admin_bot.is_admin(message.from_user.id):
        await message.answer("❌ No tienes permisos para usar este bot.")
        return
    
    await message.answer(
        "🤖 **Bot de Administración Zoolbot**\n\n"
        "Bienvenido al panel de administración. Usa los botones para navegar:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Mostrar estadísticas"""
    if not await admin_bot.is_admin(message.from_user.id):
        return
    
    stats = await admin_bot.get_user_stats()
    text = (
        f"📊 **Estadísticas del Bot**\n\n"
        f"👥 **Usuarios totales:** {stats['total_users']}\n"
        f"🟢 **Activos hoy:** {stats['active_today']}\n"
        f"🚫 **Baneados:** {stats['banned_users']}\n"
        f"💎 **Diamantes totales:** {stats['total_diamonds']:,}\n"
        f"🕒 **Última actualización:** {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await message.answer(text, parse_mode="Markdown")

# Callback handlers
@dp.callback_query(Text("main_menu"))
async def callback_main_menu(callback: types.CallbackQuery):
    """Volver al menú principal"""
    await callback.message.edit_text(
        "🤖 **Panel de Administración**\n\nSelecciona una opción:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(Text("stats"))
async def callback_stats(callback: types.CallbackQuery):
    """Mostrar estadísticas"""
    stats = await admin_bot.get_user_stats()
    text = (
        f"📊 **Estadísticas del Bot**\n\n"
        f"👥 **Usuarios totales:** {stats['total_users']}\n"
        f"🟢 **Activos hoy:** {stats['active_today']}\n"
        f"🚫 **Baneados:** {stats['banned_users']}\n"
        f"💎 **Diamantes totales:** {stats['total_diamonds']:,}\n"
        f"🕒 **Actualizado:** {datetime.now().strftime('%H:%M:%S')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Actualizar", callback_data="stats"))
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(Text("users_menu"))
async def callback_users_menu(callback: types.CallbackQuery):
    """Menú de usuarios"""
    await callback.message.edit_text(
        "👥 **Gestión de Usuarios**\n\nSelecciona una opción:",
        reply_markup=get_users_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(Text("search_user"))
async def callback_search_user(callback: types.CallbackQuery, state: FSMContext):
    """Buscar usuario por ID"""
    await callback.message.edit_text(
        "🔍 **Buscar Usuario**\n\nEnvía el ID de Telegram del usuario:"
    )
    await state.set_state(UserManagementStates.waiting_user_id)
    await callback.answer()

@dp.callback_query(Text("list_users"))
async def callback_list_users(callback: types.CallbackQuery):
    """Listar usuarios recientes"""
    users = list(db.users.find().sort("created_at", -1).limit(10))
    
    if not users:
        text = "❌ No hay usuarios registrados."
    else:
        text = "👥 **Últimos 10 usuarios registrados:**\n\n"
        for i, user in enumerate(users, 1):
            status = "🚫" if user.get("is_banned") else "✅"
            text += (
                f"{i}. {status} **{user.get('first_name', 'N/A')}**\n"
                f"   ID: `{user['telegram_id']}`\n"
                f"   💎: {user.get('diamonds', 0):,}\n"
                f"   📅: {user['created_at'].strftime('%d/%m/%Y')}\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="users_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(Text("tasks_menu"))
async def callback_tasks_menu(callback: types.CallbackQuery):
    """Menú de tareas"""
    await callback.message.edit_text(
        "📝 **Gestión de Tareas**\n\nSelecciona una opción:",
        reply_markup=get_tasks_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(Text("new_task"))
async def callback_new_task(callback: types.CallbackQuery, state: FSMContext):
    """Crear nueva tarea"""
    await callback.message.edit_text(
        "➕ **Nueva Tarea**\n\nEnvía el título de la tarea:"
    )
    await state.set_state(TaskStates.waiting_title)
    await callback.answer()

@dp.callback_query(Text("list_tasks"))
async def callback_list_tasks(callback: types.CallbackQuery):
    """Listar tareas"""
    tasks = await admin_bot.get_all_tasks()
    
    if not tasks:
        text = "❌ No hay tareas creadas."
    else:
        text = "📝 **Lista de Tareas:**\n\n"
        for i, task in enumerate(tasks, 1):
            status = "✅" if task.get("is_active") else "❌"
            text += (
                f"{i}. {status} **{task['title']}**\n"
                f"   💎 Recompensa: {task['reward']:,}\n"
                f"   🔗 URL: {task['url'][:50]}...\n"
                f"   📅 Creada: {task['created_at'].strftime('%d/%m/%Y')}\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="tasks_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(Text("announcement"))
async def callback_announcement(callback: types.CallbackQuery, state: FSMContext):
    """Enviar anuncio"""
    await callback.message.edit_text(
        "📢 **Enviar Anuncio**\n\nEscribe el mensaje que quieres enviar a todos los usuarios:"
    )
    await state.set_state(AnnouncementStates.waiting_message)
    await callback.answer()

@dp.callback_query(Text("maintenance"))
async def callback_maintenance(callback: types.CallbackQuery):
    """Toggle modo mantenimiento"""
    admin_bot.maintenance_mode = not admin_bot.maintenance_mode
    status = "activado" if admin_bot.maintenance_mode else "desactivado"
    
    text = f"🔧 **Modo Mantenimiento**\n\nEstado: {status.upper()}"
    
    builder = InlineKeyboardBuilder()
    toggle_text = "Desactivar" if admin_bot.maintenance_mode else "Activar"
    builder.row(InlineKeyboardButton(text=f"🔧 {toggle_text}", callback_data="maintenance"))
    builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer(f"Modo mantenimiento {status}")

# Message handlers para estados
@dp.message(UserManagementStates.waiting_user_id)
async def process_user_search(message: types.Message, state: FSMContext):
    """Procesar búsqueda de usuario"""
    try:
        user_id = int(message.text)
        user = await admin_bot.get_user_by_id(user_id)
        
        if user:
            status = "🚫 Baneado" if user.get("is_banned") else "✅ Activo"
            referrals = len(user.get("referrals", []))
            
            text = (
                f"👤 **Información del Usuario**\n\n"
                f"**Nombre:** {user.get('first_name', 'N/A')} {user.get('last_name', '')}\n"
                f"**Usuario:** @{user.get('username', 'N/A')}\n"
                f"**ID:** `{user['telegram_id']}`\n"
                f"**Estado:** {status}\n"
                f"**💎 Diamantes:** {user.get('diamonds', 0):,}\n"
                f"**👥 Referidos:** {referrals}\n"
                f"**📅 Registrado:** {user['created_at'].strftime('%d/%m/%Y %H:%M')}\n"
                f"**🕒 Última actividad:** {user.get('last_active', 'N/A')}"
            )
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💎 Modificar Balance", callback_data=f"mod_balance_{user_id}"),
                InlineKeyboardButton(text="🚫 Ban/Unban", callback_data=f"toggle_ban_{user_id}")
            )
            builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="users_menu"))
            
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        else:
            await message.answer("❌ Usuario no encontrado.")
            
    except ValueError:
        await message.answer("❌ ID inválido. Debe ser un número.")
    
    await state.clear()

@dp.message(TaskStates.waiting_title)
async def process_task_title(message: types.Message, state: FSMContext):
    """Procesar título de tarea"""
    await state.update_data(title=message.text)
    await message.answer("📝 Ahora envía la descripción de la tarea:")
    await state.set_state(TaskStates.waiting_description)

@dp.message(TaskStates.waiting_description)
async def process_task_description(message: types.Message, state: FSMContext):
    """Procesar descripción de tarea"""
    await state.update_data(description=message.text)
    await message.answer("💎 Envía la recompensa en diamantes (solo números):")
    await state.set_state(TaskStates.waiting_reward)

@dp.message(TaskStates.waiting_reward)
async def process_task_reward(message: types.Message, state: FSMContext):
    """Procesar recompensa de tarea"""
    try:
        reward = int(message.text)
        if reward < 0:
            await message.answer("❌ La recompensa debe ser un número positivo.")
            return
            
        await state.update_data(reward=reward)
        await message.answer("🔗 Envía el enlace/URL de la tarea:")
        await state.set_state(TaskStates.waiting_url)
    except ValueError:
        await message.answer("❌ La recompensa debe ser un número válido.")

@dp.message(TaskStates.waiting_url)
async def process_task_url(message: types.Message, state: FSMContext):
    """Procesar URL de tarea"""
    data = await state.get_data()
    
    try:
        task_id = await admin_bot.create_task(
            title=data['title'],
            description=data['description'],
            reward=data['reward'],
            url=message.text
        )
        
        text = (
            f"✅ **Tarea Creada Exitosamente**\n\n"
            f"**Título:** {data['title']}\n"
            f"**Descripción:** {data['description']}\n"
            f"**Recompensa:** {data['reward']:,} 💎\n"
            f"**URL:** {message.text}\n"
            f"**ID:** `{task_id}`"
        )
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error al crear la tarea: {str(e)}")
    
    await state.clear()

@dp.message(AnnouncementStates.waiting_message)
async def process_announcement(message: types.Message, state: FSMContext):
    """Procesar anuncio"""
    await message.answer("📢 Enviando anuncio a todos los usuarios...")
    
    result = await admin_bot.send_announcement(message.text)
    
    text = (
        f"📢 **Anuncio Enviado**\n\n"
        f"✅ **Enviados:** {result['sent']}\n"
        f"❌ **Fallidos:** {result['failed']}\n"
        f"📝 **Mensaje:** {message.text[:100]}..."
    )
    
    await message.answer(text, parse_mode="Markdown")
    await state.clear()

# Callback handlers dinámicos
@dp.callback_query(lambda c: c.data.startswith("mod_balance_"))
async def callback_modify_balance(callback: types.CallbackQuery, state: FSMContext):
    """Modificar balance de usuario"""
    user_id = int(callback.data.split("_")[2])
    await state.update_data(target_user_id=user_id)
    
    await callback.message.edit_text(
        f"💎 **Modificar Balance**\n\n"
        f"Usuario ID: `{user_id}`\n\n"
        f"Envía el cambio de balance:\n"
        f"• `+1000` para agregar 1000 diamantes\n"
        f"• `-500` para quitar 500 diamantes\n"
        f"• `=2000` para establecer en 2000 diamantes"
    )
    await state.set_state(UserManagementStates.waiting_balance_change)
    await callback.answer()

@dp.message(UserManagementStates.waiting_balance_change)
async def process_balance_change(message: types.Message, state: FSMContext):
    """Procesar cambio de balance"""
    data = await state.get_data()
    user_id = data['target_user_id']
    
    try:
        change_text = message.text.strip()
        
        if change_text.startswith('+'):
            amount = int(change_text[1:])
            operation = "add"
        elif change_text.startswith('-'):
            amount = int(change_text[1:])
            operation = "subtract"
        elif change_text.startswith('='):
            amount = int(change_text[1:])
            operation = "set"
        else:
            amount = int(change_text)
            operation = "add" if amount >= 0 else "subtract"
            amount = abs(amount)
        
        success = await admin_bot.update_user_balance(user_id, amount, operation)
        
        if success:
            user = await admin_bot.get_user_by_id(user_id)
            await message.answer(
                f"✅ **Balance Actualizado**\n\n"
                f"Usuario: {user.get('first_name', 'N/A')}\n"
                f"Operación: {operation}\n"
                f"Cantidad: {amount:,} 💎\n"
                f"Balance actual: {user.get('diamonds', 0):,} 💎"
            )
        else:
            await message.answer("❌ Error al actualizar el balance.")
            
    except ValueError:
        await message.answer("❌ Formato inválido. Usa +1000, -500, o =2000")
    
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("toggle_ban_"))
async def callback_toggle_ban(callback: types.CallbackQuery):
    """Alternar ban de usuario"""
    user_id = int(callback.data.split("_")[2])
    user = await admin_bot.get_user_by_id(user_id)
    
    if not user:
        await callback.answer("❌ Usuario no encontrado", show_alert=True)
        return
    
    is_banned = user.get("is_banned", False)
    
    if is_banned:
        success = await admin_bot.unban_user(user_id)
        action = "desbaneado"
    else:
        success = await admin_bot.ban_user(user_id, "Baneado por administrador")
        action = "baneado"
    
    if success:
        await callback.answer(f"✅ Usuario {action} exitosamente", show_alert=True)
        
        # Actualizar mensaje
        user = await admin_bot.get_user_by_id(user_id)
        status = "🚫 Baneado" if user.get("is_banned") else "✅ Activo"
        referrals = len(user.get("referrals", []))
        
        text = (
            f"👤 **Información del Usuario**\n\n"
            f"**Nombre:** {user.get('first_name', 'N/A')} {user.get('last_name', '')}\n"
            f"**Usuario:** @{user.get('username', 'N/A')}\n"
            f"**ID:** `{user['telegram_id']}`\n"
            f"**Estado:** {status}\n"
            f"**💎 Diamantes:** {user.get('diamonds', 0):,}\n"
            f"**👥 Referidos:** {referrals}\n"
            f"**📅 Registrado:** {user['created_at'].strftime('%d/%m/%Y %H:%M')}"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💎 Modificar Balance", callback_data=f"mod_balance_{user_id}"),
            InlineKeyboardButton(text="🚫 Ban/Unban", callback_data=f"toggle_ban_{user_id}")
        )
        builder.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="users_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await callback.answer("❌ Error al cambiar el estado del usuario", show_alert=True)

# Error handler mejorado
@dp.error()
async def error_handler(event, exception):
    """Manejar errores"""
    logger.error(f"Error in bot: {exception}")
    return True

async def main():
    """Función principal"""
    logger.info("🤖 Starting Zoolbot Admin Bot...")
    
    # Verificar configuración
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logger.error("❌ BOT_TOKEN not configured")
        return
    
    if not MONGO_URI:
        logger.error("❌ MONGODB_URI not configured")
        return
    
    # Verificar conexión a la base de datos
    try:
        db.command('ping')
        logger.info("✅ MongoDB connection verified")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return
    
    # Crear índices si no existen
    try:
        db.users.create_index("telegram_id", unique=True)
        db.tasks.create_index("created_at")
        db.transactions.create_index([("user_id", 1), ("created_at", -1)])
        logger.info("✅ Database indexes verified")
    except Exception as e:
        logger.warning(f"⚠️ Index warning: {e}")
    
    # Iniciar polling
    try:
        logger.info("🚀 Bot started successfully")
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        await bot.session.close()
        logger.info("🔌 Bot session closed")

if __name__ == '__main__':
    asyncio.run(main())
