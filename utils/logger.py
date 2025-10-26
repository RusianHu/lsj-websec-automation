"""
日志工具模块
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """配置日志系统"""
    # 移除默认的 handler
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.app.log_level,
        colorize=True,
    )
    
    # 添加文件输出
    log_file = settings.app.logs_dir / "app_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.app.log_level,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )
    
    return logger


# 初始化日志
log = setup_logger()

