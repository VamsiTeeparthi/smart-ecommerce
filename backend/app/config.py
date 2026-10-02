from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./ecommerce.db"
    secret_key: str = "change-this-secret-key"
    cors_origins: str = "http://localhost:5173"  # comma-separated list of allowed frontend URLs
    access_token_expire_minutes: int = 60
    payment_provider: str = "demo"
    shipping_provider: str = "demo"
    email_provider: str = "demo"
    sms_provider: str = "demo"
    storage_provider: str = "demo"
    geocoding_provider: str = "demo"
    stripe_secret_key: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    sendgrid_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    google_maps_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
