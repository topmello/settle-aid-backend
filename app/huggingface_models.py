
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
from pathlib import Path
from PIL import Image
from typing import Optional
from itertools import chain

embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


parent_path = Path(__file__).parent.parent

feedcards_dir = parent_path / "data" / "images" / "feedcards"

location_types = [d for d in feedcards_dir.iterdir() if d.is_dir()]

location_images = {
    "landmark": [],
    "restaurant": [],
    "grocery": [],
    "pharmacy": []
}

location_images_name = {
    "landmark": [],
    "restaurant": [],
    "grocery": [],
    "pharmacy": []
}

for location in location_types:
    # Get all image paths for the current location type
    image_paths = list(location.glob("*.jpg"))
    for image_path in image_paths:

        location_images[location.stem].append(Image.open(image_path))
        location_images_name[location.stem].append(image_path.stem)


def get_similar_image(text: str, location_type: Optional[str] = None):

    if not location_type:
        images = list(chain(*location_images.values()))
        names = list(chain(*location_images_name.values()))
    else:
        images = location_images[location_type]
        names = location_images_name[location_type]

    inputs = clip_processor(text=[text],
                            images=images,
                            return_tensors="pt",
                            padding=True)

    outputs = names[clip_model(
        **inputs).logits_per_image.argmax(dim=0).item()
    ]

    return outputs
