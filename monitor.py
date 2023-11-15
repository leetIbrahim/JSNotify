import requests
import hashlib
import os
import difflib
import jsbeautifier
from telegram import Bot
from dotenv import load_dotenv
import io
import re

load_dotenv() 

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

download_directory = "downloaded_js"
html_diff_directory = "html_diffs"

os.makedirs(download_directory, exist_ok=True)
os.makedirs(html_diff_directory, exist_ok=True)


def get_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def download_js(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading {url}: {str(e)}")
        return None

def save_file(content, filename):
    with open(filename, 'w') as file:
        file.write(content)

def beautify_js(js_content):
    options = jsbeautifier.default_options()
    options.indent_size = 2
    return jsbeautifier.beautify(js_content, options)


def is_within_block_comment(line, is_inside_comment):
    if '/*' in line and '*/' in line:
        return is_inside_comment 
    elif '/*' in line:
        return True 
    elif '*/' in line:
        return False  
    return is_inside_comment

def generate_html_diff(old_file, new_file):
    with open(old_file, 'r') as f1, open(new_file, 'r') as f2:
        old_lines = f1.readlines()
        new_lines = f2.readlines()

    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    in_block_comment = False
    significant_changes = False
    filtered_diff = [] 

    for line in diff:
        original_line = line[2:]  
        line_type = line[0:2]   

        if '/*' in original_line and '*/' in original_line:
            continue  
        elif '/*' in original_line:
            in_block_comment = True  
            continue
        elif '*/' in original_line and in_block_comment:
            in_block_comment = False  
            continue
        elif in_block_comment:
            continue

        if '//' in original_line and original_line.strip().startswith('//'):
            continue  

        filtered_diff.append(line) 

        if line_type in ('- ', '+ ') and not original_line.strip().startswith('//'):
            significant_changes = True

    if not significant_changes:
        return None

    old_content = []
    new_content = []
    change_links = []
    change_id = 1

    for line in filtered_diff:
        if line.startswith('- ') or line.startswith('+ '):
            change_span = f'<span id="change{change_id}" style="background-color: {"#ffdddd" if line.startswith("- ") else "#ddffdd"};">{line[2:]}</span><br>'
            if line.startswith('- '):
                old_content.append(change_span)
            else:
                new_content.append(change_span)
            change_links.append(f'<a href="#change{change_id}">Change {change_id}</a>')
            change_id += 1
        elif line.startswith('  '):
            old_content.append(line[2:] + '<br>')
            new_content.append(line[2:] + '<br>')

    style = """
    <style>
        body { font-family: Arial, sans-serif; }
        .container { display: flex; flex-wrap: wrap; }
        .column { width: 50%; padding: 10px; box-sizing: border-box; overflow-y: auto; max-height: 500px; }
        .change { background-color: #f8f9fa; padding: 5px; margin-bottom: 5px; border-radius: 5px; }
        .old { border-right: solid 1px #ddd; }
        .change span { display: block; padding: 2px 5px; }
        .removed { background-color: #ffe8e8; }
        .added { background-color: #e8ffe8; }
    </style>
    """

    navigation_bar = '<div style="margin-bottom: 20px;">' + ' | '.join(change_links) + '</div>'

    old_html = '<div class="column old"><pre>' + ''.join(old_content) + '</pre></div>'
    new_html = '<div class="column new"><pre>' + ''.join(new_content) + '</pre></div>'

    combined_html = style + navigation_bar + '<div class="container">' + old_html + new_html + '</div>' + navigation_bar

    return combined_html

def sanitize_filename(url):
    """
    Sanitize the URL to create a safe filename.
    Replace non-alphanumeric characters with underscores.
    """
    return "".join([c if c.isalnum() else "_" for c in url])

def get_latest_file(url, directory):
    """
    Get the latest downloaded file for a given URL.
    """
    sanitized_url = sanitize_filename(url)
    files = [f for f in os.listdir(directory) if f.startswith(sanitized_url)]
    if not files:
        return None
    return os.path.join(directory, sorted(files)[-1])

def send_to_telegram(html_diff, filename):
    with io.BytesIO(html_diff.encode('utf-8')) as diff_file:
        diff_file.name = filename
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'document': diff_file
        }
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument',
            files={'document': diff_file},
            data={'chat_id': TELEGRAM_CHAT_ID}
        )
        if not response.ok:
            print(f"Error sending to Telegram: {response.text}")

def monitor_js(url):
    content = download_js(url)
    if content is None:
        return

    content = beautify_js(content)
    sanitized_url = sanitize_filename(url)
    hash_object = hashlib.md5(content.encode())
    filename = f"{sanitized_url}_{hash_object.hexdigest()}.js"
    file_path = os.path.join(download_directory, filename)

    if os.path.exists(file_path):
        print(f"No changes detected in {url}.")
        return

    save_file(content, file_path)
#    print(f"New version of {url} detected and saved as {filename}")

    previous_file = get_latest_file(url, download_directory, exclude_current=filename)

    if previous_file:
        html_diff = generate_html_diff(previous_file, file_path)
        if html_diff:  
            diff_filename = f"diff_{os.path.basename(previous_file)}_vs_{filename}.html"
            send_to_telegram(html_diff, diff_filename)
            print(f"New version of {url} has detected and sent it to Telegram")
            os.remove(previous_file)
        else:
            print(f"No significant changes detected in {url}.")
            os.remove(file_path)
    else:
        print(f"This is the first download of {url}.")



def get_latest_file(url, directory, exclude_current=None):
    """
    Get the latest downloaded file for a given URL, excluding the current file.
    """
    sanitized_url = sanitize_filename(url)
    files = [f for f in os.listdir(directory) if f.startswith(sanitized_url) and f != exclude_current]
    if not files:
        return None
    return os.path.join(directory, sorted(files)[-1])


def main():
    print("JavaScript Change Detector")
    print("This script monitors JavaScript files for changes and sends notifications for significant updates.")

    file_path = input("Enter the path to the file containing URLs to monitor: ")
    if not os.path.exists(file_path):
        print("Error: The provided file path does not exist. Please check and try again.")
        return

    try:
        urls_to_monitor = get_urls_from_file(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not urls_to_monitor:
        print("No URLs found in the file. Please provide a file with valid URLs.")
        return

    print(f"Monitoring {len(urls_to_monitor)} URLs for changes...")
    for url in urls_to_monitor:
        print(f"Checking {url}...")
        monitor_js(url)
    print("Monitoring complete.")

if __name__ == "__main__":
    main()
