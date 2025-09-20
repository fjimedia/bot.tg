from aiogram import Router
from .admin_handlers import admin_router
from .user_handlers import user_router

main_router = Router(name='main_router')
main_router.include_router(admin_router)
main_router.include_router(user_router)

__all__ = ['main_router']