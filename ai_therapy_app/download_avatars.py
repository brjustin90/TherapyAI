"""
Avatar Image Downloader for AI Therapy Application

This script downloads photorealistic avatar images from Unsplash using their public API.
The images represent diverse therapists of different genders and ethnicities.
"""

import os
import requests
import json
import time
from urllib.parse import urlencode

# Configuration
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"  # Get from https://unsplash.com/developers
AVATAR_DIR = os.path.join("static", "images", "avatars")
DEFAULT_PARAMS = {
    "per_page": 1,
    "content_filter": "high",
    "orientation": "portrait"
}

# Create avatar directory if it doesn't exist
os.makedirs(AVATAR_DIR, exist_ok=True)

# Avatar configurations to download
AVATARS = [
    # Male avatars
    {"gender": "male", "ethnicity": "caucasian", "id": "1", "name": "Michael", "filename": "male_caucasian_1.jpg", 
     "query": "professional caucasian male therapist headshot"},
    {"gender": "male", "ethnicity": "caucasian", "id": "2", "name": "James", "filename": "male_caucasian_2.jpg", 
     "query": "professional white male therapist portrait"},
    
    {"gender": "male", "ethnicity": "african", "id": "3", "name": "David", "filename": "male_african_1.jpg", 
     "query": "professional black male therapist headshot"},
    {"gender": "male", "ethnicity": "african", "id": "4", "name": "William", "filename": "male_african_2.jpg", 
     "query": "professional african american male therapist portrait"},
    
    {"gender": "male", "ethnicity": "asian", "id": "5", "name": "Robert", "filename": "male_asian_1.jpg", 
     "query": "professional asian male therapist headshot"},
    {"gender": "male", "ethnicity": "asian", "id": "6", "name": "John", "filename": "male_asian_2.jpg", 
     "query": "professional east asian male therapist portrait"},
    
    {"gender": "male", "ethnicity": "hispanic", "id": "7", "name": "Carlos", "filename": "male_hispanic_1.jpg", 
     "query": "professional hispanic male therapist headshot"},
    {"gender": "male", "ethnicity": "hispanic", "id": "8", "name": "Miguel", "filename": "male_hispanic_2.jpg", 
     "query": "professional latino male therapist portrait"},
    
    {"gender": "male", "ethnicity": "middle_eastern", "id": "9", "name": "Ahmed", "filename": "male_middle_eastern_1.jpg", 
     "query": "professional middle eastern male therapist headshot"},
    {"gender": "male", "ethnicity": "middle_eastern", "id": "10", "name": "Ali", "filename": "male_middle_eastern_2.jpg", 
     "query": "professional arab male therapist portrait"},
    
    {"gender": "male", "ethnicity": "south_asian", "id": "11", "name": "Raj", "filename": "male_south_asian_1.jpg", 
     "query": "professional indian male therapist headshot"},
    {"gender": "male", "ethnicity": "south_asian", "id": "12", "name": "Vikram", "filename": "male_south_asian_2.jpg", 
     "query": "professional south asian male therapist portrait"},
    
    # Female avatars
    {"gender": "female", "ethnicity": "caucasian", "id": "13", "name": "Emily", "filename": "female_caucasian_1.jpg", 
     "query": "professional caucasian female therapist headshot"},
    {"gender": "female", "ethnicity": "caucasian", "id": "14", "name": "Sarah", "filename": "female_caucasian_2.jpg", 
     "query": "professional white female therapist portrait"},
    
    {"gender": "female", "ethnicity": "african", "id": "15", "name": "Zoe", "filename": "female_african_1.jpg", 
     "query": "professional black female therapist headshot"},
    {"gender": "female", "ethnicity": "african", "id": "16", "name": "Maya", "filename": "female_african_2.jpg", 
     "query": "professional african american female therapist portrait"},
    
    {"gender": "female", "ethnicity": "asian", "id": "17", "name": "Lucy", "filename": "female_asian_1.jpg", 
     "query": "professional asian female therapist headshot"},
    {"gender": "female", "ethnicity": "asian", "id": "18", "name": "Michelle", "filename": "female_asian_2.jpg", 
     "query": "professional east asian female therapist portrait"},
    
    {"gender": "female", "ethnicity": "hispanic", "id": "19", "name": "Sofia", "filename": "female_hispanic_1.jpg", 
     "query": "professional hispanic female therapist headshot"},
    {"gender": "female", "ethnicity": "hispanic", "id": "20", "name": "Isabella", "filename": "female_hispanic_2.jpg", 
     "query": "professional latina female therapist portrait"},
    
    {"gender": "female", "ethnicity": "middle_eastern", "id": "21", "name": "Yasmin", "filename": "female_middle_eastern_1.jpg", 
     "query": "professional middle eastern female therapist headshot"},
    {"gender": "female", "ethnicity": "middle_eastern", "id": "22", "name": "Fatima", "filename": "female_middle_eastern_2.jpg", 
     "query": "professional arab female therapist portrait"},
    
    {"gender": "female", "ethnicity": "south_asian", "id": "23", "name": "Priya", "filename": "female_south_asian_1.jpg", 
     "query": "professional indian female therapist headshot"},
    {"gender": "female", "ethnicity": "south_asian", "id": "24", "name": "Deepa", "filename": "female_south_asian_2.jpg", 
     "query": "professional south asian female therapist portrait"},
]

def download_avatar(avatar_config):
    """Download a single avatar image from Unsplash"""
    print(f"Downloading {avatar_config['name']} ({avatar_config['gender']}, {avatar_config['ethnicity']})...")
    
    # Skip if already downloaded
    filepath = os.path.join(AVATAR_DIR, avatar_config["filename"])
    if os.path.exists(filepath):
        print(f"  ✓ Already downloaded: {avatar_config['filename']}")
        return True
    
    # Prepare API request
    params = DEFAULT_PARAMS.copy()
    params["query"] = avatar_config["query"]
    
    url = f"https://api.unsplash.com/search/photos?{urlencode(params)}"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    
    try:
        # Make API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check if results found
        if not data.get("results") or len(data["results"]) == 0:
            print(f"  ✗ No results found for query: {avatar_config['query']}")
            return False
        
        # Get first result and download image
        photo_url = data["results"][0]["urls"]["regular"]
        photo_response = requests.get(photo_url)
        photo_response.raise_for_status()
        
        # Save image to file
        with open(filepath, "wb") as f:
            f.write(photo_response.content)
            
        print(f"  ✓ Downloaded: {avatar_config['filename']}")
        
        # Be nice to the API and avoid rate limits
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"  ✗ Error downloading {avatar_config['filename']}: {str(e)}")
        return False

def create_placeholder_image(avatar_config):
    """Create a placeholder image when real image can't be downloaded"""
    print(f"Creating placeholder for {avatar_config['filename']}...")
    
    filepath = os.path.join(AVATAR_DIR, avatar_config["filename"])
    
    try:
        # Download a placeholder from placehold.co
        gender = avatar_config["gender"].capitalize()
        ethnicity = avatar_config["ethnicity"].capitalize()
        name = avatar_config["name"]
        
        placeholder_url = f"https://placehold.co/400x600/e9ecef/495057?text={name}%0A{gender}%20{ethnicity}%20Therapist"
        placeholder_response = requests.get(placeholder_url)
        placeholder_response.raise_for_status()
        
        # Save placeholder to file
        with open(filepath, "wb") as f:
            f.write(placeholder_response.content)
            
        print(f"  ✓ Created placeholder: {avatar_config['filename']}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error creating placeholder {avatar_config['filename']}: {str(e)}")
        return False

def main():
    """Main function to download all avatar images"""
    print(f"Downloading {len(AVATARS)} avatar images...")
    
    success_count = 0
    for avatar in AVATARS:
        if UNSPLASH_ACCESS_KEY != "your_unsplash_access_key":
            # Try to download from Unsplash
            if download_avatar(avatar):
                success_count += 1
                continue
        
        # If Unsplash download fails or no API key, create placeholder
        if create_placeholder_image(avatar):
            success_count += 1
    
    print(f"\nDownloaded {success_count}/{len(AVATARS)} avatar images")
    print(f"Avatar images saved to: {os.path.abspath(AVATAR_DIR)}")
    
    # Write avatar metadata to JSON file for reference
    metadata_file = os.path.join(AVATAR_DIR, "avatars_metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(AVATARS, f, indent=2)
    
    print(f"Avatar metadata saved to: {metadata_file}")

if __name__ == "__main__":
    main() 