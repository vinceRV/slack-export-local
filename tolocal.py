import os
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import hashlib
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the inclusion list of allowed domains
inclusion_list = ['slack.com', 'slack-edge.com', 'gravatar.com']

def create_copy(src, dst, resource_dir):
    if os.path.isdir(src):
        if not os.path.exists(dst):
            os.makedirs(dst)
        files = os.listdir(src)
        for f in files:
            create_copy(os.path.join(src, f), os.path.join(dst, f), resource_dir)
    else:
        shutil.copy2(src, dst)
        logging.info(f"Copied file from {src} to {dst}")
        if src.lower().endswith('.html'):
            process_html(dst, resource_dir)

def process_html(file_path, resource_dir):
    logging.info(f"Processing HTML file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    base_dir = os.path.dirname(file_path)

    for tag, attr in [('img', 'src'), ('link', 'href'), ('a', 'href')]:
        for element in soup.find_all(tag):
            url = element.get(attr)
            if url and not url.startswith('data:'):  # Ignore base64 encoded images
                if is_allowed_domain(url):
                    local_path = download_resource(url, resource_dir)
                    if local_path:
                        element[attr] = os.path.relpath(local_path, base_dir)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))
    logging.info(f"Finished processing HTML file: {file_path}")

def is_allowed_domain(url):
    domain = urlparse(url).netloc
    for allowed_domain in inclusion_list:
        if domain.endswith(allowed_domain):
            return True
    logging.info(f"Skipped resource from {url} (not in allowed domains)")
    return False

def download_resource(url, resource_dir):
    try:
        parsed_url = urlparse(url)
        resource_path = parsed_url.path
        hashed_path = hashlib.md5(resource_path.encode()).hexdigest()
        local_filename = os.path.join(resource_dir, hashed_path + os.path.splitext(resource_path)[1])

        if not os.path.exists(local_filename):
            logging.info(f"Downloading resource from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logging.info(f"Downloaded resource to {local_filename}")
        else:
            logging.info(f"Resource already exists: {local_filename}")
        return local_filename
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy and process files from source to destination folder.')
    parser.add_argument('src_folder', type=str, help='Source folder path')
    parser.add_argument('dst_folder', type=str, help='Destination folder path')
    args = parser.parse_args()

    resource_dir = os.path.join(args.dst_folder, 'resources')

    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)

    logging.info(f"Starting copy from {args.src_folder} to {args.dst_folder}")
    create_copy(args.src_folder, args.dst_folder, resource_dir)
    logging.info("Copy operation completed")
