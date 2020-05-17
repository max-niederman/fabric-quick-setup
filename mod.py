# Mod.py
import requests
import jenkinsapi
from jenkinsapi.jenkins import Jenkins
import json
import re
from bs4 import BeautifulSoup
from pprint import pprint

def download(url: str, out='', name=None):
    r = requests.get(url)
    filename = out + name if name else out + url.split('/')[-1]
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
        if 'dependencies' in self.resource:
            self.install_dependencies(mc_dir, mc_version)
        
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
                
            # Filter assets for Minecraft version and get latest asset
            if not self.resource['version-agnostic']:
                assets = [x for x in assets if mc_version in x['name']]
            if assets:
                asset = assets[-1]
            else:
                raise ModVersionNotFoundError('No assets were found for this version of Minecraft')
            
            download(asset['browser_download_url'], out=f'{mc_dir}\mods\\')
        
        elif self.resource['type'] == 'fabric':
            # Snapshot to eventual release version
            fabric_versions = requests.get('https://meta.fabricmc.net/v2/versions/game').json()
            mc_versions = [v['version'] for v in fabric_versions]
            f = re.compile('\d.\d\d$')
            seen_version = False
            if f.match(mc_version):
                release_version = mc_version
            else:
                for version in mc_versions:
                    if version == mc_version:
                        seen_version = True
                    
                    if f.match(version) and seen_version:
                        release_version = version[:-1] + str(int(version[-1]) + 1)
                        break
            
            # Get Jenkins Artifact and Download
            jenkins = Jenkins('https://jenkins.modmuss50.me')
            job = jenkins.get_job(f'Fabric/API {release_version}')
            build = job.get_last_good_build()
            artifacts = build.get_artifact_dict()
            artifact = list(artifacts.values())[-1]
            artifact.save_to_dir(f'{mc_dir}\mods\\')
                    
        
        elif self.resource['type'] == 'optifine':
            # Get optifine.net downloads page
            with requests.get('https://www.optifine.net/downloads') as r:
                downloads_page = BeautifulSoup(r.text, 'lxml')
            
            # Get list of mirrors and get mirror of latest release for Minecraft version
            mirrors = downloads_page.select('.downloadLineMirror')
            mirrors = [x for x in mirrors if mc_version in x.a['href']]
            if mirrors:
                mirror = mirrors[0]
            else:
                raise ModVersionNotFoundError('No releases were found for this version of Minecraft')

            # Get mirror page
            with requests.get(mirror.a['href']) as r:
                mirror_page = BeautifulSoup(r.text, 'lxml')
            
            # Get download link
            download_elem = mirror_page.find('span', {'id': 'Download'})
            download(f'https://optifine.net/{download_elem.a["href"]}', out=f'{mc_dir}\mods\\', name=download_elem.get_text()[11:-1])

        elif self.resource['url']:
            download(self.resource['url'], out=f'{mc_dir}\mods\\')
        
        else:
            raise InvalidModResourceError('No valid mod resource data was found')
    
    def install_dependencies(self, mc_dir: str, mc_version: str):
        for dependency in self.resource['dependencies']:
            mod = Mod(dependency['resource'])
            mod.install(mc_dir, mc_version)