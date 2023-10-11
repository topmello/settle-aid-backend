from ..redis import get_redis_images_db
from ..exceptions import ImageNotFoundException
from ..schemas import TipImage
from pathlib import Path
import base64
from fastapi import APIRouter, Depends
import aioredis


router = APIRouter(
    prefix='/tip',
    tags=["Tip"]
)

image_path = Path(__file__).parent.parent.parent / 'data' / 'images' / 'tip'


@router.get('/image/{image_name}', response_model=TipImage)
async def get_image(
    image_name: str,
    r: aioredis.Redis = Depends(get_redis_images_db)
):

    if not (image_path / image_name).exists():
        raise ImageNotFoundException()

    encoded_image = await r.get(f"tip:{image_name}")

    if encoded_image:
        return TipImage(image_name=image_name, image=encoded_image)

    with open(image_path / image_name, 'rb') as f:
        binary_data = f.read()
        base64_encoded = base64.b64encode(binary_data)
        encoded_image = base64_encoded.decode('utf-8')
        await r.set(f"tip:{image_name}", encoded_image, expire=60*60*24)

    return TipImage(image_name=image_name, image=encoded_image)
