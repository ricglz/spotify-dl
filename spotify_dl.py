"""
spotify_dl.py

Downloads music from spotify using youtube as an intermidiate
"""
#!/usr/local/bin/python3

from argparse import ArgumentParser
from os import system
from typing import Tuple
from traceback import print_exc
from urllib3 import PoolManager

from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

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

#=======================
#   Other constants
#=======================
http = PoolManager()
TrackInfo = Tuple[str, str, str]

#=======================
#   Actual code
#=======================
def write_to_file(response):
    """ONLY FOR DEBUGGING: Creates an html file with the response"""
    txt_file = open('test.html', 'w')
    txt_file.write(response)
    txt_file.close()

def get_youtube_link(track_info: TrackInfo):
    """Search in youtube using the track_name as query"""
    fields = {'search_query': ' '.join(track_info)}
    url = 'https://www.youtube.com/results'
    response = http.request('GET', url, fields=fields).data
    write_to_file(response.decode('utf-8'))
    soup = BeautifulSoup(response, 'html.parser')
    first_link = soup.find('a', attrs={'class':'yt-thumbnail'})['href']
    return f'https://youtube.com{first_link}'

def get_track_info(track) -> TrackInfo:
    """Gets the track name using its track id"""
    artist_name = track['artists'][0]['name']
    # album_name = track['album']['name']
    track_name = track['name']
    return track_name, artist_name

def get_playlist_tracks(playlist_id: str):
    """Get tracks that are in a spotify playlist"""
    items = spotify.playlist(playlist_id)['tracks']['items']
    get_track_from_item = lambda item: item['track']
    return list(map(get_track_from_item, items))

def download_youtube(links: [str]):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    system(f'add_music {" ".join(links)}')

def main(args):
    """Main process"""
    try:
        tracks = [spotify.track(args.track[0])] if args.track else \
                 get_playlist_tracks(args.playlist[0]) if args.playlist else None
        if tracks is None:
            print(f'{ERROR} use --help for help')
            return
        track_infos = list(map(get_track_info, tracks))
        links = list(map(get_youtube_link, track_infos))
        print(links[0])
        # download_youtube(links)
    except spotipy.SpotifyException as err:
        print(f'{ERROR} {err}')
        if args.traceback:
            print_exc()

if __name__ == "__main__":
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--verbose', action='store_true', help='verbose flag' )
    parser.add_argument('--traceback', action='store_true', help="enable traceback")
    parser.add_argument('--track', nargs=1, help="spotify track id")
    parser.add_argument('--playlist', nargs=1, help="spotify track id")

    main(parser.parse_args())
