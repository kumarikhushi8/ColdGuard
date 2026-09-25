from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "postgresql://coldguard:coldguard_secret@localhost:5432/coldguard"
    secret_key: str = "dev_secret_key_change_in_production_min_32_chars"
    api_url: str = "http://localhost:8000"

    # Alert thresholds
    temp_warning: float = 6.0
    temp_critical: float = 10.0
    humidity_warning: float = 85.0
    humidity_critical: float = 92.0
    ethylene_warning: float = 1.0
    ethylene_critical: float = 5.0

    # Simulator (enable for demo/Render deployment)
    run_simulator: bool = True

    # WhatsApp Business API
    whatsapp_enabled: bool = False
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_template_en: str = "cold_storage_alert"
    whatsapp_template_hi: str = "cold_storage_alert_hi"
    whatsapp_template_mr: str = "cold_storage_alert_mr"

    # SMS (fast2sms)
    sms_enabled: bool = False
    sms_api_key: str = ""
    sms_sender_id: str = "COLDGD"

    # Notification behaviour
    notify_critical_only: bool = False
    alert_cooldown_minutes: int = 30

    # JWT Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # OTP (SMS-based for farmers)
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 3

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
