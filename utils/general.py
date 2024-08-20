import os
from pathlib import Path
import requests

def download_uri(uri, dir_path):
    # Ensure dir_path is a Path object
    dir_path = Path(dir_path)

    # Create filename from the URI
    filename = os.path.basename(uri.split("?")[0])

    # Combine dir_path and filename correctly
    save_path = dir_path / filename

    # Download the file
    with requests.get(uri, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {filename} to {save_path}")
