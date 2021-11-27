#!/usr/local/bin/python3
"""
spotify_dl.py

Downloads music from spotify using youtube as an intermidiate
"""

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from os import environ
from subprocess import call
from traceback import print_exc
from typing import Tuple, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
import spotipy

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.firefox import GeckoDriverManager

from storage import Storage

#=======================
#   Terminal Colors
#=======================
RED     = "\033[31m"
GREEN   = "\033[32m"
BLUE    = "\033[34m"
YELLOW  = "\033[36m"
DEFAULT = "\033[0m"

ACTION  = BLUE + "[+] " + DEFAULT
ERROR   = RED + "[+] " + DEFAULT
OK      = GREEN + "[+] " + DEFAULT

#=======================
#   Spotify application
#=======================
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
USER_ID = environ.get('SPOTIFY_USER_ID', '123456789')

#=======================
#   Spotify application
#=======================
YT_DEVELOPER_KEY = environ.get('YT_DEVELOPER_KEY', '')
youtube = build('youtube', 'v3', developerKey=YT_DEVELOPER_KEY).search()

options = webdriver.FirefoxOptions()
options.headless = True
try:
    driver = webdriver.Firefox(options=options)
except WebDriverException:
    driver = webdriver.Firefox(GeckoDriverManager().install(), options=options)

#=======================
#   Other constants
#=======================
TrackInfo = Tuple[str, str, str]
storage = Storage(environ.get('SPOTIFY_DATABASE', ''))

#=======================
#   Actual code
#=======================
def write_to_file(response):
    """ONLY FOR DEBUGGING: Creates an html file with the response"""
    with open('test.html', 'w') as txt_file:
        txt_file.write(response.decode('utf-8'))

def get_tracks(args) -> List[dict]:
    if args.track:
        return [spotify.track(args.track[0])]
    if args.playlist:
        return get_playlist_tracks(args.playlist[0])
    return None

def get_playlist_tracks(playlist_id: str):
    """Get tracks that are in a spotify playlist"""
    items = spotify.user_playlist_tracks(USER_ID, playlist_id)['items']
    offset = 100
    total_items = []
    while len(items) == 100:
        print('Getting 100 tracks more')
        total_items += items
        items = spotify.user_playlist_tracks(USER_ID, playlist_id, offset=offset)['items']
        offset += 100
    total_items += items
    tracks = [item['track'] for item in tqdm(total_items, 'Getting playlist tracks')]
    return tracks

def download_youtube(links: [str]):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    call(['add_music'] + links)

def scrap_youtube_link(query: str):
    """Scrap youtube content to search for the first link"""
    fields = urlencode({'search_query': query})
    driver.get(f'https://www.youtube.com/results?{fields}')
    content = driver.page_source.encode('utf-8').strip()
    soup = BeautifulSoup(content, 'html.parser')
    first_elem = soup.find('a', id='video-title')
    if first_elem is None:
        tqdm.write(f'{query}: Was None')
        return ''
    try:
        first_link = first_elem['href']
    except KeyError:
        tqdm.write(f'{query}: {first_elem.attrs}')
        return ''
    return f'https://youtube.com{first_link}'

def search_youtube_link(query: str):
    """Search for the id using google api and return the link"""
    results = youtube.list(q=query, part='id,snippet', maxResults=5).execute()
    for result in results.get('items', []):
        id_object = result['id']
        if id_object['kind'] == 'youtube#video':
            actual_id = id_object['videoId']
            return f'https://youtube.com/watch?v={actual_id}'
    return ''

def get_track_info(track) -> TrackInfo:
    """Gets the track name using its track id"""
    artist_name = track['artists'][0]['name']
    track_name = track['name']
    return track_name, artist_name

def get_youtube_link(track):
    """
    Gets the youtube link either by scrapping the results site
    or by using the google api
    """
    track_info = get_track_info(track)
    query = ' '.join(track_info)
    # try:
    #     return search_youtube_link(query)
    # except HttpError:
    #     return scrap_youtube_link(query)
    return scrap_youtube_link(query)

def get_link(track: dict) -> str:
    try:
        link = storage.get_link(track['id'])
    except KeyError:
        link = get_youtube_link(track)
        if link != '':
            storage.store_link(track['id'], link)
    return link

def get_links(tracks: List[dict]):
    with ThreadPoolExecutor() as executor:
        pool_iterator = tqdm(
            executor.map(get_link, tracks),
            desc='Getting links',
            total=len(tracks),
        )
        links = list(filter(lambda x: x != '', pool_iterator))
    return links

def main(args):
    """Main process"""
    try:
        tracks = get_tracks(args)
        if tracks is None:
            print(f'{ERROR} use --help for help')
            return
        links = get_links(tracks)
        download_youtube(links)
    except spotipy.SpotifyException as err:
        print(f'{ERROR} {err}')
        if args.traceback:
            print_exc()
    finally:
        print(f'{ACTION} closing driver')
        driver.close()

if __name__ == "__main__":
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--verbose', action='store_true', help='verbose flag' )
    parser.add_argument('--traceback', action='store_true', help="enable traceback")
    parser.add_argument('--track', nargs=1, help="spotify track id")
    parser.add_argument('--playlist', nargs=1, help="spotify track id")

    main(parser.parse_args())
