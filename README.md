# 🤖 Zoolbot - Telegram Mini App

Sistema completo de tareas, misiones e intervenciones con moneda virtual para Telegram, incluyendo depósitos y retiros de TON, sistema de referidos y conexión de billetera.

## 🌟 Características

- ✅ **Mini App de Telegram** - Interfaz web integrada
- 💎 **Sistema de Diamantes** - Moneda virtual interna
- 🪙 **Integración TON** - Depósitos y retiros reales
- 👥 **Sistema de Referidos** - Bonificaciones por invitar amigos
- 📱 **Conexión de Billetera** - Compatible con TonKeeper
- 🎯 **Tareas y Misiones** - Sistema gamificado
- 🤖 **Bot de Administración** - Panel completo de gestión
- 📊 **Analytics** - Estadísticas detalladas

## 🏗️ Arquitectura

\`\`\`
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mini App      │    │   Admin Bot     │    │   MongoDB       │
│   (Next.js)     │◄──►│   (Python)      │◄──►│   Database      │
│   Web Service   │    │   Worker        │    │   Atlas         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
\`\`\`

## 🚀 Despliegue en Render

### Prerrequisitos

1. **Cuenta en Render** - [render.com](https://render.com)
2. **Repositorio en GitHub** - Código subido
3. **MongoDB Atlas** - Base de datos configurada
4. **Bot de Telegram** - Token de @BotFather

### Paso 1: Preparar el Repositorio

\`\`\`bash
# Clonar o descargar el proyecto
git clone https://github.com/tu-usuario/zoolbot-miniapp.git
cd zoolbot-miniapp

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Subir a GitHub
git add .
git commit -m "Initial commit - Zoolbot project"
git push origin main
\`\`\`

### Paso 2: Configurar MongoDB Atlas

1. Crear cluster en [MongoDB Atlas](https://cloud.mongodb.com)
2. Configurar usuario y contraseña
3. Obtener connection string
4. Agregar IP de Render a whitelist: `0.0.0.0/0`

### Paso 3: Crear Bot de Telegram

\`\`\`bash
# Hablar con @BotFather en Telegram
/newbot
# Seguir instrucciones y obtener token

# Configurar Web App
/setmenubutton
# Seleccionar tu bot
# Texto: 🎮 Abrir Zoolbot
# URL: https://tu-app.onrender.com (configurar después)
\`\`\`

### Paso 4: Desplegar en Render

#### A. Web Service (Mini App)

1. **Crear Web Service:**
   - Dashboard → "New +" → "Web Service"
   - Conectar repositorio de GitHub
   - Configurar:

\`\`\`yaml
Name: zoolbot-miniapp
Environment: Node
Build Command: npm install && npm run build
Start Command: npm start
\`\`\`

2. **Variables de Entorno:**

\`\`\`env
NODE_ENV=production
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/zoolbot?retryWrites=true&w=majority
\`\`\`

#### B. Background Worker (Admin Bot)

1. **Crear Background Worker:**
   - Dashboard → "New +" → "Background Worker"
   - Mismo repositorio
   - Configurar:

\`\`\`yaml
Name: zoolbot-admin-bot
Environment: Python 3
Build Command: pip install -r scripts/requirements.txt
Start Command: python scripts/telegram_admin_bot.py
\`\`\`

2. **Variables de Entorno:**

\`\`\`env
BOT_TOKEN=tu_bot_token_aqui
ADMIN_ID=tu_telegram_user_id
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/zoolbot?retryWrites=true&w=majority
DB_NAME=zoolbot
\`\`\`

#### C. Job de Setup (Base de Datos)

1. **Crear Job:**
   - Dashboard → "New +" → "Job"
   - Mismo repositorio
   - Configurar:

\`\`\`yaml
Name: zoolbot-db-setup
Environment: Python 3
Build Command: pip install -r scripts/requirements.txt
Start Command: python scripts/database_setup.py
\`\`\`

2. **Variables de Entorno:**

\`\`\`env
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/zoolbot?retryWrites=true&w=majority
DB_NAME=zoolbot
\`\`\`

### Paso 5: Orden de Despliegue

1. **Primero:** Ejecutar Job de setup (una sola vez)
2. **Segundo:** Desplegar Web Service
3. **Tercero:** Desplegar Background Worker

### Paso 6: Configurar Telegram Bot

Una vez desplegado el Web Service, obtendrás una URL como:
`https://zoolbot-miniapp.onrender.com`

Configurar en @BotFather:
\`\`\`bash
/setmenubutton
# Seleccionar tu bot
# Texto: 🎮 Abrir Zoolbot
# URL: https://zoolbot-miniapp.onrender.com
\`\`\`

## 🔧 Configuración Local (Desarrollo)

### Prerrequisitos

- Node.js 18+
- Python 3.8+
- MongoDB (local o Atlas)

### Instalación

\`\`\`bash
# Instalar dependencias de Node.js
npm install

# Instalar dependencias de Python
pip install -r scripts/requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Setup de base de datos
python scripts/database_setup.py

# Ejecutar en desarrollo
npm run dev

# En otra terminal, ejecutar bot admin
python scripts/telegram_admin_bot.py
\`\`\`

## 📊 Monitoreo y Logs

### Verificar Despliegues

1. **Web Service:**
   - Render Dashboard → Web Service → Logs
   - Verificar: "✅ Ready on http://localhost:3000"

2. **Background Worker:**
   - Render Dashboard → Worker → Logs
   - Verificar: "🚀 Bot started successfully"

3. **Probar API:**
\`\`\`bash
curl https://tu-app.onrender.com/api/tasks
\`\`\`

### Logs Importantes

\`\`\`bash
# Web Service
✅ Connected to MongoDB
✅ Server running on port 3000

# Admin Bot
✅ MongoDB connection verified
🚀 Bot started successfully
✅ Database indexes verified
\`\`\`

## 🐛 Solución de Problemas

### Errores Comunes

**1. Build falla en Render:**
\`\`\`bash
# Verificar package.json
"engines": {
  "node": "18.x"
}
\`\`\`

**2. MongoDB no conecta:**
\`\`\`bash
# Verificar:
- Connection string correcto
- IP whitelisted en Atlas (0.0.0.0/0)
- Usuario y contraseña correctos
\`\`\`

**3. Bot no responde:**
\`\`\`bash
# Verificar:
- BOT_TOKEN correcto
- Variables de entorno configuradas
- Worker ejecutándose sin errores
\`\`\`

**4. Mini App no carga:**
\`\`\`bash
# Verificar:
- URL configurada en @BotFather
- Web Service desplegado correctamente
- HTTPS habilitado
\`\`\`

## 💰 Costos Estimados

### Render Pricing

- **Web Service:** Free tier (suficiente para empezar)
- **Background Worker:** Starter Plan ($7/mes)
- **Jobs:** Gratis (solo setup inicial)
- **Total:** ~$7/mes

### MongoDB Atlas

- **M0 Cluster:** Gratis (512MB)
- **M2 Cluster:** $9/mes (2GB) - Recomendado para producción

## 🔄 Actualizaciones

### Deploy Automático

Render se actualiza automáticamente con cada push a `main`:

\`\`\`bash
git add .
git commit -m "Update features"
git push origin main
# Render desplegará automáticamente
\`\`\`

### Actualizaciones Manuales

1. **Redeploy Web Service:** Dashboard → Manual Deploy
2. **Restart Worker:** Dashboard → Restart
3. **Run Job:** Solo si hay cambios en DB

## 📚 API Endpoints

### Autenticación
- `POST /api/auth/telegram` - Autenticar usuario

### Usuarios
- `GET /api/user?telegram_id=123` - Obtener usuario
- `POST /api/user/wallet` - Conectar billetera

### Tareas
- `GET /api/tasks?user_id=123` - Listar tareas
- `POST /api/tasks/complete` - Completar tarea

### Transacciones
- `GET /api/transactions?user_id=123` - Historial

## 🛡️ Seguridad

### Variables de Entorno

Nunca commitear:
- `BOT_TOKEN`
- `MONGODB_URI`
- Claves privadas

### Validaciones

- Verificación de usuario de Telegram
- Rate limiting en APIs
- Validación de transacciones
- Sanitización de inputs

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

### Documentación
- [Render Docs](https://render.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [TON Documentation](https://ton.org/docs)

### Contacto
- **Telegram:** @tu_usuario
- **Email:** tu@email.com
- **Issues:** GitHub Issues

## 🎯 Roadmap

- [ ] Integración con más billeteras
- [ ] Sistema de niveles avanzado
- [ ] Marketplace de NFTs
- [ ] Staking de tokens
- [ ] Programa de afiliados
- [ ] Panel web de administración
- [ ] API pública
- [ ] SDK para desarrolladores

---

**¡Hecho con ❤️ para la comunidad TON!**
