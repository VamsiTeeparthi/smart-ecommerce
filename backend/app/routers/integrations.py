from fastapi import APIRouter, UploadFile, File
from ..services.integrations import storage, geocoding

router=APIRouter(prefix="/api/integrations",tags=["Integrations"])

@router.post("/image-upload")
async def image_upload(file:UploadFile=File(...)):
    return storage.upload(file.filename)

@router.get("/geocode")
def geocode(address:str): return geocoding.geocode(address)
