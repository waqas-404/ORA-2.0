import asyncio
import os
import time
from time import sleep
from PIL import Image
from dotenv import get_key
from huggingface_hub import InferenceClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
FLAG_FILE = os.path.join(BASE_DIR, "Frontend", "Files", "ImageGeneration.data")
DATA_DIR = os.path.join(BASE_DIR, "Data")

HF_TOKEN = get_key(ENV_PATH, "HuggingFaceAPIKey")

client = InferenceClient(
    provider="fal-ai",
    api_key=HF_TOKEN,
)

def open_images(prompt):
    prompt_key = prompt.replace(" ", "_")
    files = [f"{prompt_key}{i}.jpg" for i in range(1, 3)]

    for name in files:
        image_path = os.path.join(DATA_DIR, name)

        if not os.path.exists(image_path):
            print("Not found:", image_path)
            continue

        try:
            with Image.open(image_path) as im:
                im.verify()
        except Exception as e:
            print("Invalid image:", image_path, e)
            continue

        print("Opening:", image_path)
        os.startfile(image_path)
        time.sleep(0.5)


async def generate_single_image(prompt: str, index: int):
    full_prompt = f"photorealistic image of {prompt}, ultra detailed, professional photography"
    print(f"DEBUG sending prompt: '{full_prompt}'")

    image = await asyncio.to_thread(
        client.text_to_image,
        full_prompt,
        model="Tongyi-MAI/Z-Image-Turbo",
    )

    out_path = os.path.join(DATA_DIR, f"{prompt.replace(' ', '_')}{index}.jpg")
    image.save(out_path)
    print(f"Saved: {out_path}")


async def generate_images(prompt: str):
    tasks = [
        asyncio.create_task(generate_single_image(prompt, i))
        for i in range(1, 3)
    ]
    await asyncio.gather(*tasks)


def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)


# Main loop
while True:
    try:
        with open(FLAG_FILE, "r") as f:
            Data: str = f.read().strip()

        # rsplit ensures prompts with commas (e.g. "tall, dark") don't break parsing
        Prompt, Status = Data.rsplit(",", 1)
        Prompt = Prompt.strip()
        Status = Status.strip()

        if Status == "True":
            print(f"Generating images for: '{Prompt}'")
            GenerateImages(prompt=Prompt)

            with open(FLAG_FILE, "w", encoding="utf-8") as f:
                f.write("False,False")
            break

        else:
            sleep(1)

    except Exception as e:
        print("Loop error:", e)
        sleep(1)