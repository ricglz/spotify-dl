#!/usr/local/bin/python3

from argparse import ArgumentParser
from json import loads
from os import system, environ
from subprocess import PIPE, Popen
from traceback import print_exc
from urllib.parse import quote
from urllib3 import PoolManager
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from bs4 import BeautifulSoup

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
spotify = spotipy.Spotify(SpotifyClientCredentials())

#=======================
#   Other constants
#=======================
http = PoolManager()

#=======================
#   Actual code
#=======================

def search_youtube(track_name: str):
    """Search in youtube using the track_name as query"""
    text_to_search = track_name
    query = quote(text_to_search)
    url = f'https://www.youtube.com/results?search_query={query}'
    response = http.request('GET', url)
    soup = BeautifulSoup(response.data, 'html.parser')
    first_link = soup.findAll(attrs={'class': 'yt-uix-tile-link'})[0]['href']
    return f'https://youtube.com{first_link}'

def download_data(process: str):
    """Downloads the data from a process and stores it in a tmp file"""
    proc = Popen(process, shell=True, stdout=PIPE)
    return proc.stdout.read()

def get_data_from_process(process: str):
    """Gets data downloaded from a process"""
    tmp = download_data(process)
    return loads(tmp)

def get_track_name(track_id: str):
    """Gets the track name using its track id"""
    print(f'{ACTION} getting track name')
    name = spotify.track(track_id)['name']
    print(f'{OK} name is {name}')
    return name

def download_youtube(link: str):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    system(f'add_music {link}')

def header():
    """Header information"""
    print(RED + "@ spotify-dl.py version 0.0.1")
    print(YELLOW + "@ author : Naper")
    print(BLUE + "@ Designed for OSx/linux")
    print("" + DEFAULT)

def main(args):
    """Main process"""
    try:
        header()
        if args.track:
            name = get_track_name(args.track[0])
            link = search_youtube(name)
            download_youtube(link)
        else:
            print(ERROR + "use --help for help")
    except Exception as err:
        print(ERROR + "An HTTP error occurred\n")
        print(type(err))
        if args.traceback:
            print_exc()

if __name__ == "__main__":
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--verbose', action='store_true', help='verbose flag' )
    parser.add_argument('--traceback', action='store_true', help="enable traceback")
    parser.add_argument('--track', nargs=1, help="spotify track id")

    main(parser.parse_args())
