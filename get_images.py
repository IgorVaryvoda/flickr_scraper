import os
import argparse
from pathlib import Path
import requests
from urllib.parse import urlencode
import time
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Flickr API credentials
flickr_key = os.getenv("FLICKR_KEY")
flickr_secret = os.getenv("FLICKR_SECRET")

def fetch_places():
    response = supabase.table("places").select("id,name,country_id,score").order('score', desc=True).execute()
    return response.data


def download_uri(uri, dir_path):
    dir_path = Path(dir_path)
    filename = os.path.basename(uri.split("?")[0])
    save_path = dir_path / filename

    with requests.get(uri, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {filename} to {save_path}")

def get_urls(search="honeybees on flowers", n=15, download=False, dir_path=None):
    t = time.time()

    base_url = "https://api.flickr.com/services/rest/"
    params = {
        "method": "flickr.photos.search",
        "api_key": flickr_key,
        "text": search,
        "sort": "relevance",
        "per_page": min(n, 500),
        "extras": "url_o",
        "format": "json",
        "nojsoncallback": 1
    }

    url = f"{base_url}?{urlencode(params)}"

    if download:
        if dir_path is None:
            dir_path = Path.cwd() / "images" / search.replace(" ", "_")
        dir_path.mkdir(parents=True, exist_ok=True)

    urls = []
    try:
        response = requests.get(url)
        data = response.json()

        if 'photos' in data and 'photo' in data['photos']:
            for i, photo in enumerate(data['photos']['photo']):
                if i < n:
                    try:
                        photo_url = photo.get('url_o')

                        if not photo_url:
                            photo_url = f"https://farm{photo['farm']}.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_b.jpg"

                        if download:
                            download_uri(photo_url, str(dir_path))

                        urls.append(photo_url)
                        print(f"{i+1}/{n} {photo_url}")
                    except Exception as e:
                        print(f"{i+1}/{n} error: {str(e)}")
                else:
                    break
        else:
            print("No photos found in the API response.")

    except Exception as e:
        print(f"Error fetching photos: {str(e)}")

    print(
        f"Done. ({time.time() - t:.1f}s)"
        + (f"\nAll images saved to {dir_path}" if download else "")
    )
    return urls

def scrape_and_save_images(place, n=10):
    place_id = place['id']
    search_term = f"{place['name']}, {place['country_id']}"

    dir_path = Path.cwd() / "images" / str(place_id)
    dir_path.mkdir(parents=True, exist_ok=True)

    print(f"Scraping images for: {search_term}")
    get_urls(search=search_term, n=n, download=True, dir_path=dir_path)

def main(n_images):
    places = fetch_places()
    for place in places:
        scrape_and_save_images(place, n_images)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="number of images per place")
    opt = parser.parse_args()

    main(opt.n)
