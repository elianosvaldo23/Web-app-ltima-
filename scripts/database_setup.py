#!/usr/bin/env python3
"""
Script para configurar la base de datos inicial de Zoolbot
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import logging

# Configuración
MONGO_URI = "mongodb+srv://zoobot:zoobot@zoolbot.6avd6qf.mongodb.net/zoolbot?retryWrites=true&w=majority&appName=Zoolbot"
DB_NAME = "zoolbot"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Configurar la base de datos inicial"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Verificar conexión
        db.command('ping')
        logger.info("✅ Conexión a MongoDB exitosa")
        
        # Crear colecciones e índices
        collections = [
            'users',
            'tasks', 
            'missions',
            'user_tasks',
            'transactions',
            'announcements',
            'settings'
        ]
        
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"✅ Colección '{collection_name}' creada")
        
        # Crear índices
        indices = [
            ('users', 'telegram_id', True),  # único
            ('users', 'referrer_id', False),
            ('users', 'created_at', False),
            ('users', 'last_active', False),
            ('tasks', 'is_active', False),
            ('tasks', 'created_at', False),
            ('user_tasks', [('user_id', 1), ('task_id', 1)], True),  # compuesto único
            ('transactions', [('user_id', 1), ('created_at', -1)], False),
            ('transactions', 'type', False),
            ('missions', 'is_active', False),
        ]
        
        for collection_name, field, unique in indices:
            try:
                if isinstance(field, list):
                    db[collection_name].create_index(field, unique=unique)
                else:
                    db[collection_name].create_index(field, unique=unique)
                logger.info(f"✅ Índice en {collection_name}.{field} creado")
            except pymongo.errors.DuplicateKeyError:
                logger.info(f"ℹ️ Índice en {collection_name}.{field} ya existe")
        
        # Insertar configuración inicial
        default_settings = {
            'maintenance_mode': False,
            'diamond_to_ton_rate': 100000,
            'referral_percentage': 0.1,
            'task_verification_timeout': 3600,  # 1 hora
            'min_withdrawal_amount': 1,  # 1 TON mínimo
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        if not db.settings.find_one():
            db.settings.insert_one(default_settings)
            logger.info("✅ Configuración inicial insertada")
        
        # Insertar tareas de ejemplo
        sample_tasks = [
            {
                'title': '🎉 Únete a nuestro canal oficial',
                'description': 'Sigue nuestro canal oficial de Telegram para recibir actualizaciones',
                'reward': 5000,
                'url': 'https://t.me/ZoolbotChannel',
                'verification_type': 'telegram_join',
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'title': '👍 Dale like a nuestra publicación',
                'description': 'Da me gusta a nuestra última publicación en el canal',
                'reward': 2500,
                'url': 'https://t.me/ZoolbotChannel',
                'verification_type': 'url_visit',
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'title': '📱 Sigue nuestro Twitter',
                'description': 'Síguenos en Twitter para más actualizaciones',
                'reward': 3000,
                'url': 'https://twitter.com/zoolbot',
                'verification_type': 'url_visit',
                'is_active': True,
                'created_at': datetime.now()
            }
        ]
        
        if db.tasks.count_documents({}) == 0:
            db.tasks.insert_many(sample_tasks)
            logger.info("✅ Tareas de ejemplo insertadas")
        
        logger.info("🎉 Base de datos configurada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error configurando la base de datos: {e}")
        raise

if __name__ == '__main__':
    setup_database()
