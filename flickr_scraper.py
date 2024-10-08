# Generated by Glenn Jocher (glenn.jocher@ultralytics.com) for https://github.com/ultralytics

import argparse
import time
import os
from pathlib import Path
import requests
from urllib.parse import urlencode

from utils.general import download_uri
import xml.etree.ElementTree as ET

key =  os.getenv("FLICKR_KEY")
secret = os.getenv("FLICKR_SECRET")




def get_urls(search="honeybees on flowers", n=10, download=False):
    t = time.time()

    # Construct the Flickr API URL
    base_url = "https://api.flickr.com/services/rest/"
    params = {
        "method": "flickr.photos.search",
        "api_key": key,
        "text": search,
        "sort": "relevance",
        "per_page": min(n, 500),  # Flickr API allows max 500 per page
        "extras": "url_o",
        "format": "json",
        "nojsoncallback": 1
    }

    url = f"{base_url}?{urlencode(params)}"

    if download:
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
                        # Try to get the original size URL
                        photo_url = photo.get('url_o')

                        # If original size is not available, construct the large size URL
                        if not photo_url:
                            photo_url = f"https://farm{photo['farm']}.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_b.jpg"

                        if download:
                            download_uri(photo_url, str(dir_path))  # Convert dir_path to string

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




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--search",
        nargs="+",
        default=["honeybees on flowers"],
        help="flickr search term",
    )
    parser.add_argument("--n", type=int, default=10, help="number of images")
    parser.add_argument("--download", action="store_true", help="download images")
    opt = parser.parse_args()

    print(f"nargs {opt.search}")
    help_url = "https://www.flickr.com/services/apps/create/apply"
    assert (
        key and secret
    ), f"Flickr API key required in flickr_scraper.py L11-12. To apply visit {help_url}"

    for search in opt.search:
        get_urls(search=search, n=opt.n, download=opt.download)
