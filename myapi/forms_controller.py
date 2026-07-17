from ninja_extra import api_controller, route
from ninja import Schema
from typing import Optional
from .models import DeletionRequest, ContactMessage

class DeletionInput(Schema):
    organization_number: str
    name: str
    email: str
    reason: Optional[str] = None

class ContactInput(Schema):
    name: str
    email: str
    phone_number: Optional[str] = None
    message: str

class SuccessSchema(Schema):
    success: bool
    message: str

@api_controller('/forms', tags=['User Forms'])
class FormsController:
    
    @route.post('/deletion', response=SuccessSchema)
    def submit_deletion(self, payload: DeletionInput):
        DeletionRequest.objects.create(**payload.dict())
        return {"success": True, "message": "Forespørselen din om sletting av data er mottatt."}

    @route.post('/contact', response=SuccessSchema)
    def submit_contact(self, payload: ContactInput):
        ContactMessage.objects.create(**payload.dict())
        return {"success": True, "message": "Takk for at du tar kontakt! Vi vil svare deg så snart som mulig."}
