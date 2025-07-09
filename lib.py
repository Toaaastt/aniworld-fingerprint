import os
import requests
from bs4 import BeautifulSoup
from typing import Literal
from html import unescape
import difflib
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

ALLOW_PRINT = True
SCRAPE_DIR = os.path.join(os.getcwd(), "scrapes")
os.makedirs(SCRAPE_DIR, exist_ok=True)

def print_event(event_type: str, message: str):
    if not ALLOW_PRINT:
        return
    if event_type == "FETCH":
        print(f"{Fore.CYAN}[FETCH]  {Style.RESET_ALL} {message}")
    elif event_type == "PROC":
        print(f"{Fore.YELLOW}[PROCESS]{Style.RESET_ALL} {message}")
    elif event_type == "SUCCESS":
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")
    elif event_type == 'PRIMARY':
        print(f"{Fore.BLUE}[PRIMARY]{Style.RESET_ALL} {message}")
    else:
        print(f"[{event_type}] {message}")

def url_to_filename(url: str) -> str:
    return os.path.join(SCRAPE_DIR, url.replace("https://", "").replace("http://", "").replace("/", "_") + ".html")

def get_cached_html(url: str) -> str:
    filename = url_to_filename(url)
    if os.path.exists(filename):
        print_event("FETCH", f"Using cached HTML from {filename}")
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    print_event("PRIMARY", f"Downloading HTML from {url}")
    response = requests.get(url)
    html = response.text
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html)
    return html

# -------- Updated Functions Using get_cached_html --------

def download_anime_thumbnail(anime_url: str, save_path: str) -> str | None:
    html = get_cached_html(anime_url).split("\n")
    image_url = ""
    for line in html:
        if "seriesCoverBox" in line:
            print_event("PROC", "Searching for cover image URL")
            image_url = 'https://aniworld.to' + line.split('data-src="')[1].split('"')[0]
            response = requests.get(image_url)
            path = os.path.join(save_path, 'cover.png')
            with open(path, 'wb') as file:
                file.write(response.content)
            print_event("SUCCESS", f"Downloaded cover image to {path}")
            return image_url
    raise Exception("Image URL not found!")

def list_available_hosters(url: str, prefered_data_lang_key: int = 1) -> list[str]:
    html_content = get_cached_html(url).split("\n")
    hoster_list = []
    print_event("PROC", "Searching for available hosters")
    for l, line in enumerate(html_content):
        if "icon " in line and "Hoster " in line and (f'data-lang-key="{prefered_data_lang_key}"' in html_content[l - 3] or f'data-lang-key="{prefered_data_lang_key}"' in html_content[l - 6]):
            h = line.split("Hoster ")[1].split('">')[0]
            if h not in hoster_list:
                hoster_list.append(h)
    print_event("SUCCESS", f"Found hosters: {hoster_list}")
    return hoster_list

def get_redirect_url_from_hoster(url: str, hoster: str, data_lang_key: int = 1) -> str | None:
    data = get_cached_html(url).split("\n")
    for l in range(len(data)):
        if 'href="/redirect/' in data[l] and "Hoster " + hoster in data[l + 2] and f'data-lang-key="{data_lang_key}"' in data[l - 4]:
            redirect_url = "https://aniworld.to" + data[l].split('href="')[1].split('"')[0]
            print_event("SUCCESS", f"Found redirect URL: {redirect_url}")
            return redirect_url

def get_anime_name_from_url(url: str) -> str:
    html_content = get_cached_html(url).split("\n")
    for line in html_content:
        if '<meta name="description" content="' in line:
            anime_name = line.split(' von ')[1].split(' und ')[0]
            return unescape(unescape(anime_name))
    return ''

def get_episode_count_from_url(url: str) -> int:
    text = get_cached_html(url)
    episode_count = 0
    type = 'movie' if 'film' in url else 'normal'
    l = 0
    while True:
        l += 1
        if (f"Folge {l}" in text and type == 'normal') or (f"Film {l}" in text and type == 'movie'):
            episode_count += 1
        else:
            break
    print_event("SUCCESS", f"Found {episode_count} episodes")
    return episode_count

def get_season_data_from_url(url: str) -> list[int]:
    response = get_cached_html(url)
    s = [] if 'Alle Filme' not in response else [0]
    idx = 0
    while True:
        idx += 1
        if f"Staffel {idx}" in response:
            s.append(idx)
        else:
            break
    return s

def get_episode_name_from_url(url: str, lan: Literal['de', 'en']) -> str:
    html = get_cached_html(url).split("\n")
    for line in html:
        if lan == "de" and '<span class="episodeGermanTitle">' in line:
            return unescape(unescape(line.split('<span class="episodeGermanTitle">')[1].split('</span>')[0].strip()))
        if lan == "en" and '<small class="episodeEnglishTitle">' in line:
            return unescape(unescape(line.split('<small class="episodeEnglishTitle">')[1].split('</small>')[0].strip()))
    return ''

def get_available_langs_from_url(url: str) -> list[str]:
    html = get_cached_html(url).split("\n")
    langs = []
    for line in html:
        if 'class="changeLanguageBox"' in line:
            if 'data-lang-key="1"' in line:
                langs.append("de")
            if 'data-lang-key="2"' in line:
                langs.append("jp-en")
            if 'data-lang-key="3"' in line:
                langs.append("jp-de")
    return langs

def get_anime_rating(url: str) -> int | None:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    rating_value = soup.find("span", itemprop="ratingValue")
    return int(rating_value.text.strip()) if rating_value else None

def get_anime_description(url: str) -> str | None:
    html = get_cached_html(url)
    if 'data-full-description="' not in html:
        return None
    return unescape(unescape(html.split('data-full-description="')[1].split('">')[0]))

def get_genres(url: str) -> list[str]:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    genres = [a.get_text(strip=True) for a in soup.select("div.genres a.genreButton")]
    return genres

def get_actors(url: str) -> list[str]:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    return [a.get_text(strip=True) for a in soup.select("li[itemprop='actor'] a span")]

def get_producers(url: str) -> list[str]:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    return [a.get_text(strip=True) for a in soup.select("li[itemprop='creator'] a span")]

def get_regisseurs(url: str) -> list[str]:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    return [a.get_text(strip=True) for a in soup.select("li[itemprop='director'] a span")]

def get_countries(url: str) -> list[str]:
    soup = BeautifulSoup(get_cached_html(url), "html.parser")
    return [a.get_text(strip=True) for a in soup.select("li[itemprop='countryOfOrigin'] a span")]

# -- Other unchanged utility functions: get_url_name_from_url, get_season_id_from_url, etc.
# You can optionally migrate those too using get_cached_html if they ever use requests.

if __name__ == "__main__":
    i = get_redirect_url_from_hoster('https://aniworld.to/anime/stream/tis-time-for-torture-princess/staffel-1/episode-1', 'VOE', 2)
    print(i)
