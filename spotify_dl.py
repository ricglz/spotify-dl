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
from typing import Iterable, Optional, Tuple, List, TypedDict

from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
from spotipy import Spotify, SpotifyException
from ytmusicapi import YTMusic

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
spotify = Spotify(client_credentials_manager=SpotifyClientCredentials())
USER_ID = environ.get('SPOTIFY_USER_ID', '123456789')

#=======================
#   Youtube application
#=======================
yt_music = YTMusic()

#=======================
#   Other constants
#=======================
storage = Storage(environ.get('SPOTIFY_DATABASE', ''))

#=======================
#   Types
#=======================
TrackInfo = Tuple[str, str]
class Artist(TypedDict):
    '''Type for an artist'''
    name: str
class Track(TypedDict):
    '''Type for a track'''
    artists: List[Artist]
    id: str
    name: str
class Item(TypedDict):
    '''Type for a track'''
    track: Track

#=======================
#   Actual code
#=======================
def get_tracks(args) -> Optional[List[Track]]:
    '''Gets a list of tracks based if is a single track or a list of them'''
    if args.track:
        track_id = args.track[0]
        track = spotify.track(track_id)
        return None if track is None else [track]
    if args.playlist:
        return get_playlist_tracks(args.playlist[0])
    return None

def safe_playlist_tracks(playlist_id: str, offset: int) -> List[Item]:
    '''Safe playlist tracks'''
    response = spotify.user_playlist_tracks(USER_ID, playlist_id, offset=offset)
    return [] if response is None else response['items']

def get_playlist_tracks(playlist_id: str) -> List[Track]:
    """Get tracks that are in a spotify playlist"""
    offset = 0
    items = safe_playlist_tracks(playlist_id, offset)
    total_items = items.copy()
    while len(items) == 100:
        print('Getting 100 tracks more')
        offset += 100
        items = safe_playlist_tracks(playlist_id, offset)
        total_items += items
    tracks = [item['track'] for item in tqdm(total_items, 'Getting playlist tracks')]
    return tracks

def scrap_youtube_link(query: str) -> str:
    """Scrap youtube content to search for the first link"""
    response = yt_music.search(query, filter='songs', limit=1)[0]
    video_id: str = response['videoId']
    video_link = f'http://youtube.com/watch?v={video_id}'
    print(video_link)
    return video_link

def get_track_info(track: Track) -> TrackInfo:
    """Gets the track name using its track id"""
    artist_name = track['artists'][0]['name']
    track_name = track['name']
    return track_name, artist_name

def get_youtube_link(track: Track):
    """
    Gets the youtube link either by scrapping the results site
    or by using the google api
    """
    track_info = get_track_info(track)
    query = ' '.join(track_info)
    return scrap_youtube_link(query)

def get_link(track: Track) -> str:
    '''Gets the link of a track'''
    try:
        link = storage.get_link(track['id'])
    except KeyError:
        link = get_youtube_link(track)
        if link != '':
            storage.store_link(track['id'], link)
    return link

def get_links(tracks: List[Track]) -> Iterable[str]:
    '''Gets the links of the tracks'''
    with ThreadPoolExecutor() as executor:
        pool_iterator = tqdm(
            executor.map(get_link, tracks),
            desc='Getting links',
            total=len(tracks),
        )
        links = set(filter(lambda x: x != '', pool_iterator))
    return links

def download_youtube(links: Iterable[str]):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    call(['add_music'] + list(links))

def main(args):
    """Main process"""
    try:
        tracks = get_tracks(args)
        if tracks is None:
            print(f'{ERROR} use --help for help')
            return
        links = get_links(tracks)
        download_youtube(links)
    except SpotifyException as err:
        print(f'{ERROR} {err}')
        if args.traceback:
            print_exc()
    finally:
        print(f'{ACTION} closing driver')

if __name__ == "__main__":
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--verbose', action='store_true', help='verbose flag' )
    parser.add_argument('--traceback', action='store_true', help="enable traceback")
    parser.add_argument('--track', nargs=1, help="spotify track id")
    parser.add_argument('--playlist', nargs=1, help="spotify track id")

    main(parser.parse_args())
