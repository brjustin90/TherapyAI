import os
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_avatar(filename, text, bg_color=(200, 200, 200)):
    # Create a 200x200 image with a background color
    img = Image.new('RGB', (200, 200), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()
    
    # Center the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (200 - text_width) // 2
    y = (200 - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    
    # Save the image
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)

def main():
    base_dir = "static/images/avatars"
    genders = ["male", "female"]
    ethnicities = ["caucasian", "african_american", "asian", "hispanic", "middle_eastern", "south_asian"]
    
    # Clean up existing avatars directory
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    for gender in genders:
        for ethnicity in ethnicities:
            # Create two avatars for each combination
            for i in range(1, 3):
                filename = f"{base_dir}/{gender}/{gender}_{ethnicity}_{i}.jpg"
                text = f"{gender.title()}\n{ethnicity.title()}\n#{i}"
                create_avatar(filename, text)

if __name__ == "__main__":
    main()
    print("Avatar images created successfully!") 