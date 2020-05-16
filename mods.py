import requests
import wget
import json

class Mod:
    def __init__(self, url: str):
        self.url = url
    
    def install(self, mc_dir: str):
        wget.download(self.url, out=f'{mc_dir}\mods\\')

class GitHub(Mod):
    def __init__(self, repo: str, release=None):
        super().__init__(f'https://github/{repo}')
        self.repo, self.release = repo, release

    def install(self, mc_dir: str, mc_version: str):
        # Get Latest Asset for Minecraft Version
        if self.release:
            release = requests.get(f'https://api.github.com/repos/{repo}/releases/{release}').json()
            asset = release.assets[-1]
        else:
            # Get all release assets for repo
            releases = requests.get(f'https://api.github.com/repos/{repo}/releases').json()
            assets = list()
            for release in releases.reverse():
                assets += release.assets
            
            # Filter assets for Minecraft Version
            assets = filter(lambda x : self.mc_version in x.name, assets)
            
            # Get latest asset
            asset = assets[-1]
        
        wget.download(asset.browser_download_url, out=f'{mc_dir}\mods\\')