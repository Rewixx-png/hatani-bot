from aiogram import Router
from app.handlers.admin import router as admin_router
from app.handlers.messages import router as messages_router

router = Router()

router.include_router(admin_router)
router.include_router(messages_router)