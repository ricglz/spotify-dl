#!/usr/bin/python

from argparse import ArgumentParser
from json import loads
from os import system
from subprocess import PIPE, Popen
from traceback import print_exc
from urllib.parse import quote
from urllib3 import PoolManager

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
OK      =  GREEN + "[+] " + DEFAULT

#=======================
#   Spotify application
#=======================
CLIENT_ID=""
CALL_BACK_URL=""

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

def get_track_name_process(track_id: str, access_token: str):
    """Gets the track name process based on the track id and the access token"""
    process = 'curl -sS -X GET "https://api.spotify.com/v1/tracks/'
    process += f'{track_id}?market=ES" -H "Authorization: Bearer '
    process += f'{access_token}"'
    return process

def get_track_name(track_id: str, access_token: str):
    """ get the spotify track name from id """
    print(f'{ACTION} getting track name')
    process = get_track_name_process(track_id, access_token)
    data = get_data_from_process(process)
    if 'error' in data:
        error_msg = data['error']['message']
        print(f"{ERROR} can't found song name")
        print(f'{ERROR} {error_msg}')
        return None
    name = data['name']
    print(f'{OK} name is {name}')
    return name

def generate_url():
    """Generate url for getting access token"""
    print(f'{ACTION} generating url for access token')
    url = f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}'
    url += f'&response_type=token&redirect_uri={CALL_BACK_URL}'
    print(f'{OK} {url}')

def get_access_token_process():
    """Gets the process to get the access token"""
    process = 'curl -sS -X GET "https://accounts.spotify.com/authorize?client_id='
    process += f'{CLIENT_ID}&response_type=token&redirect_uri={CALL_BACK_URL}'
    process += '" -H "Accept: application/json"'
    return process

def get_access_token():
    """Get access token"""
    print(f'{ACTION} getting access token')
    process = get_access_token_process()
    print(get_data_from_process(process))

def download_youtube(link: str):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    system(f'add_music {link}')

def header():
    """ header informations """
    print(RED + "@ spotify-dl.py version 0.0.1")
    print(YELLOW + "@ author : Naper")
    print(BLUE + "@ Designed for OSx/linux")
    print("" + DEFAULT)

def main(args):
    """Main process"""
    try:
        header()
        if args.gen_url:
            generate_url()
        else:
            if args.dl and args.access_token and args.dl[0] == 'youtube' and args.track:
                name = get_track_name(args.track[0], args.access_token[0])
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
    parser.add_argument('--dl', nargs=1, help="set the download methode")
    parser.add_argument('--user', nargs=1, help="set the spotify login")
    parser.add_argument('--password', nargs=1, help="set the spotify password")
    parser.add_argument('--traceback', action='store_true', help="enable traceback")
    parser.add_argument(
            '--gen_url', action='store_true', help="generate url for getting access_token")
    parser.add_argument('--track', nargs=1, help="spotify track id")
    parser.add_argument('--access_token', nargs=1, help="set the access_token")
    parser.add_argument('-m', nargs=1, help="set a methode")

    main(parser.parse_args())
