#!/usr/bin/env python3
import os
import subprocess
import sys

GEN_SCRIPT = "/Volumes/MOVESPEED/Github/lipeaks_backend/.agents/skills/nektra-image-generator/scripts/generate.py"
OUT_DIR = "/Volumes/MOVESPEED/Github/lipeaks_backend/media/application/images"
API_KEY = "sk-31d3edba2a1e081282b5e9e1b4226b0b90a429da1d3d58eedb7aba73a5d51425"
BASE_URL = "https://code2alita.com/v1"

BADGES = [
    ("level_silver.png", "A 3D glossy game UI badge icon of a silver medal with ribbon, shiny chrome metallic silver texture, transparent background, isolated, PNG, high quality, vector asset style"),
    ("level_gold.png", "A 3D glossy game UI badge icon of a gold medal with ribbon, sparkling metallic gold texture, transparent background, isolated, PNG, high quality, vector asset style"),
    ("level_platinum.png", "A 3D glossy game UI badge icon of a platinum shield medal, glowing pale cyan platinum metallic texture, transparent background, isolated, PNG, high quality, vector asset style"),
    ("level_diamond.png", "A 3D glossy game UI badge icon of a crystal blue diamond gemstone, sparkling facets, transparent background, isolated, PNG, high quality, vector asset style"),
    ("level_crown.png", "A 3D glossy game UI badge icon of a royal golden crown with jewels, majestic king crown, transparent background, isolated, PNG, high quality, vector asset style"),
]

for filename, prompt in BADGES:
    target_path = os.path.join(OUT_DIR, filename)
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        print(f"Skipping {filename}, already exists.")
        continue
    print(f"Generating {filename}...")
    cmd = [
        sys.executable, GEN_SCRIPT,
        "--api-key", API_KEY,
        "--base-url", BASE_URL,
        "--prompt", prompt,
        "--output", target_path,
        "--size", "1024x1024"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Successfully generated {filename}")
    else:
        print(f"Failed to generate {filename}: {res.stderr}")

print("Batch generation completed.")
