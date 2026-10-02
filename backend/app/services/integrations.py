import uuid
from . import __init__  # keeps package import explicit

class PaymentService:
    def create_payment(self, amount: float, method: str):
        return {"provider": "demo", "payment_id": "PAY-" + uuid.uuid4().hex[:10], "status": "PAID", "amount": amount}

class ShippingService:
    def create_shipment(self, order_id: int, address: str):
        return {"tracking_number": "TRK-" + uuid.uuid4().hex[:10].upper(), "status": "LABEL_CREATED"}

    def track(self, tracking_number: str):
        return {"tracking_number": tracking_number, "status": "IN_TRANSIT", "events": ["Shipment created", "Package picked up"]}

class EmailService:
    def send(self, to: str, subject: str, body: str):
        return {"provider": "demo", "sent": True, "to": to, "subject": subject}

class SMSService:
    def send(self, phone: str, message: str):
        return {"provider": "demo", "sent": True, "phone": phone, "message": message}

class StorageService:
    def upload(self, filename: str):
        return {"provider": "demo", "url": f"https://placehold.co/600x400?text={filename}"}

class GeocodingService:
    def geocode(self, address: str):
        return {"provider": "demo", "address": address, "latitude": 17.3850, "longitude": 78.4867}

payment = PaymentService()
shipping = ShippingService()
email = EmailService()
sms = SMSService()
storage = StorageService()
geocoding = GeocodingService()
