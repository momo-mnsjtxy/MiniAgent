import secrets
import string
from pathlib import Path

from nonebot import get_plugin_config, logger
from pydantic import BaseModel


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password
    """
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    while True:
        password = "".join(secrets.choice(characters) for _ in range(length))
        # Ensure password contains at least one uppercase, one lowercase, one digit, and one special character
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*()" for c in password)
        ):
            return password


class Config(BaseModel):
    """
    Configuration for webui
    """

    webui_enable: bool = True
    webui_user_name: str = "admin"
    webui_password: str = ""


def save_password_to_dotenv(password: str) -> bool:
    """
    Save password to .env file
    Returns True if successful, False otherwise
    """
    try:
        env_file = Path(".env")
        lines = []

        # Read existing .env if it exists
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                lines = f.readlines()

        # Update or add WEBUI_PASSWORD
        password_line = f"WEBUI_PASSWORD={password}\n"
        webui_pass_found = False

        for i, line in enumerate(lines):
            if line.startswith("WEBUI_PASSWORD="):
                lines[i] = password_line
                webui_pass_found = True
                break

        if not webui_pass_found:
            lines.append(password_line)

        # Write back to .env
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info("WebUI密码已安全保存到.env文件")
        return True
    except Exception as e:
        logger.error(f"无法保存密码到.env文件: {e}")
        return False


def get_webui_config() -> Config:
    config = get_plugin_config(Config)

    # Generate secure password if default/empty password is detected
    if not config.webui_password or config.webui_password == "admin123":
        # This is a security improvement - generate a secure random password
        # In production, this should be handled during setup process
        secure_password = generate_secure_password()
        config.webui_password = secure_password

        # Attempt to save to .env for persistence
        if save_password_to_dotenv(secure_password):
            logger.warning(
                f"WebUI密码已自动生成并保存到.env文件，请妥善保管：{secure_password}"
            )
            logger.warning("下次启动时将使用此密码，您可在.env文件中修改WEBUI_PASSWORD")
        else:
            logger.critical(
                f"【重要安全提醒】WebUI密码已生成但无法持久化：{secure_password}"
            )
            logger.critical(
                "下次启动将生成新密码，请在.bot启动后查看日志获取密码"
            )

    return config


def get_or_create_admin_password() -> str:
    """
    Get the current admin password, creating a new secure one if needed
    """
    config = get_webui_config()
    return config.webui_password


def reset_admin_password() -> str:
    """
    Reset admin password to a new secure random password
    Returns the new password
    """
    config = get_webui_config()
    new_password = generate_secure_password()
    config.webui_password = new_password
    save_password_to_dotenv(new_password)
    logger.info("管理员密码已重置")
    return new_password
