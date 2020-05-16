# Mod.py
import requests
import json
from pprint import pprint

def download(url: str, out=''):
    r = requests.get(url)
    filename = out + url.split('/')[-1]
    with open(filename, 'wb') as outfile:
        outfile.write(r.content)

# Errors
class InvalidModResourceError(Exception):
    pass

class ModVersionNotFoundError(InvalidModResourceError):
    pass

# Mod Class
class Mod:
    def __init__(self, resource: dict):
        self.resource = resource
    
    def install(self, mc_dir: str, mc_version: str):
        if self.resource['type'] == 'github':
            # Get Latest Asset for Minecraft Version
            if self.resource['release']:
                release = requests.get(f'https://api.github.com/repos/{self.resource["repo"]}/releases/{self.resource["release"]}').json()
                assets = release.assets
            else:
                # Get all release assets for repo
                releases = requests.get(f'https://api.github.com/repos/{self.resource["repo"]}/releases').json()
                assets = list()
                releases.reverse()
                for release in releases:
                    assets += release['assets']
                
            # Filter assets for Minecraft Version
            assets = [asset for asset in assets if mc_version in asset['name']]
                
            # Get latest asset
            if assets:
                asset = assets[-1]
            else:
                raise ModVersionNotFoundError('No assets were found for this version of Minecraft')
            
            download(asset['browser_download_url'], out=f'{mc_dir}\mods\\')
        
        elif self.resource['url']:
            download(self.resource['url'], out=f'{mc_dir}\mods\\')
        
        else:
            raise InvalidModResourceError('No valid mod resource data was found')