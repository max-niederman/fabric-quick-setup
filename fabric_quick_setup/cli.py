#!/usr/bin/env python
# Main.py
from fabric_quick_setup.mod import Mod, InvalidModResourceError, ModVersionNotFoundError
import json
import os
import platform
import sys
import subprocess
import requests
import click
import six
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt, style_from_dict)
from pyfiglet import figlet_format
from pprint import pprint

try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

try:
    from termcolor import colored
except ImportError:
    colored = None

# Terminal Styling
style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: ''
})

class Log:
    def __init__(self, queue=[]):
        self.queue = queue
    
    def print_log(self, string, color, font='slant', figlet=False):
        if colored:
            if not figlet:
                six.print_(colored(string, color))
            else:
                six.print_(colored(figlet_format(
                    string, font=font), color))
        else:
            six.print_(string)
    
    def queue_log(self, color, font='slant', figlet=False):
        self.queue.append((color, font, figlet))
    
    def print_queue(self):
        for log in self.queue:
            self.print_log(*log)

log = Log()

def clean_exit(color: str):
    log.print_log('Exiting...', color)
    sys.exit()

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_fabric_installer(dir):
    fabric_installers = requests.get('https://meta.fabricmc.net/v2/versions/installer').json()
    r = requests.get(fabric_installers[0]['url'])
    filename = f'{dir}\\fabric-installer.jar'
    with open(filename, 'wb') as outfile:
        outfile.write(r.content)
    return filename

def install_fabric(installer_path, mc_dir, mc_version, server): 
    if server:
        installer = subprocess.run(['java', 
            '-jar', 
            installer_path, 
            'server',
            '-snapshot',
            '-mcversion',
            mc_version,
            '-dir',
            mc_dir,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)
    else:
        installer = subprocess.run(['java', 
            '-jar', 
            installer_path, 
            'client',
            '-snapshot',
            '-noprofile',
            '-mcversion',
            mc_version,
            '-dir',
            mc_dir,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)
    if installer.stderr:
        questions = [
                {
                    'type': 'confirm',
                    'message': f'Fabric Installer errored. Should I continue with the mod installation anyway? y/N',
                    'name': 'continue',
                    'default': False,
                }
            ]
        answers = prompt(questions, style=style)
        if answers['continue']:
            return
        else:
            clean_exit('red')

def delete_mods(mc_dir):
    mod_dir = f'{mc_dir}\\mods'
    try:
        files = [f for f in os.listdir(mod_dir)]
    except FileNotFoundError:
        return
    for f in files:
        os.remove(os.path.join(mod_dir, f))

def install_mod(mod_dict, mc_modded_dir, mc_version):
    mod = Mod(mod_dict['resource'])
    try:
        mod.install(mc_modded_dir, mc_version)
    except ModVersionNotFoundError:
        if 'alternative' in mod_dict:
            questions = [
                {
                    'type': 'confirm',
                    'message': f'{mod_dict["name"]} is not available for {mc_version}. Should I try installing {mod_dict["alternative"]["name"]} instead? Y/n',
                    'name': 'install',
                    'default': True,
                }
            ]
            answers = prompt(questions, style=style)
            if answers['install']:
                install_mod(mod_dict['alternative'], mc_modded_dir, mc_version)
        else:
            raise

def resolve_dependencies(mod_ids: set, mod_list: list):
    mods = [mod for mod in mod_list if mod['id'] in mod_ids]
    dependencies = set()
    for mod in mods:
        if 'dependencies' in mod:
            dependencies.update(mod['dependencies'])
    return dependencies

def ask_mc_dirs(mc_default_path, server):
    client_questions = [
        {
            'type': 'input',
            'name': 'mc_dir',
            'message': 'Enter Minecraft Directory',
            'default': lambda answers : f'{mc_default_path}'
        },
        {
            'type': 'input',
            'name': 'mc_modded_dir',
            'message': 'Enter Modded Minecraft Directory.',
            'default': lambda answers : answers['mc_dir']
        }
    ]
    server_questions = [
        {
            'type': 'input',
            'name': 'mc_dir',
            'message': 'Enter Server Directory',
            'default': lambda answers : f'{mc_default_path}'
        },
        {
            'type': 'input',
            'name': 'mc_modded_dir',
            'message': 'Enter modded server directory. 99.99% of people should leave this at the default value.',
            'default': lambda answers : answers['mc_dir']
        }
    ]
    if server:
        answers = prompt(server_questions, style=style)
    else:
        answers = prompt(client_questions, style=style)
    return answers

def get_mc_versions():
    fabric_versions = requests.get('https://meta.fabricmc.net/v2/versions/game').json()
    mc_versions = [v['version'] for v in fabric_versions]
    return mc_versions

def ask_version():
    mc_versions = get_mc_versions()
    questions = [
        {
            'type': 'input',
            'name': 'version',
            'message': 'Enter Minecraft Version',
            'default': mc_versions[0],
            'validate': lambda val: True if val in mc_versions else f'{val} is not a valid version of Minecraft.'
        }
    ]
    answers = prompt(questions, style=style)
    return answers['version']

def ask_mods(mods, server):
    questions = {
        'type': 'checkbox',
        'message': 'Select Mods to Install',
        'name': 'mods',
        'choices': [{ 'name': mod['name'] } for mod in mods if mod['visible']['server' if server else 'client']],
    }
    answers = prompt(questions)
    return answers['mods']

@click.command()
@click.option('--debug', is_flag=True, default=False)
@click.option('--mod-list', 'mod_list_url', default='https://raw.githubusercontent.com/max-niederman/fabric-quick-setup/master/fabric_quick_setup/mods.json', type=str, help='Mod list URL.')
@click.option('--installer', 'installer_path', type=click.Path(), help='Path to Fabric Installer')
@click.option('-s', '--server', is_flag=True, default=False)
@click.option('-d', '--mc-dir', type=click.Path(), help='Minecraft directory')
@click.option('-t', '--mc-modded-dir', type=click.Path(), help='Minecraft modded directory')
@click.option('-v', '--version', 'mc_version', type=str, help='Minecraft version to install')
@click.option('-m', '--mods', 'mod_ids', type=str, multiple=True, help='Mods to install. Use this once for each mod.')
def main(debug, mod_list_url, installer_path, server, mc_dir, mc_modded_dir, mc_version, mod_ids):
    """
    CLI to install Fabric Loader and Popular Mods
    """
    log.print_log('Fabric Quick Setup', 'blue', figlet=True)
    log.print_log('Welcome to Fabric Quick Setup', 'green')

    mc_default_path = '' if server else {
        'Windows': f'{os.getenv("APPDATA")}\\.minecraft',
        'Darwin': f'{os.getenv("HOME")}/Library/Application Support/minecraft',
        'Linux': f'{os.getenv("HOME")}/.minecraft'
    }[platform.system()]

    if not mc_dir:
        mc_dirs = ask_mc_dirs(mc_default_path, server)
        mc_dir, mc_modded_dir = mc_dirs['mc_dir'], mc_dirs['mc_modded_dir']
    
    ensure_dir(mc_dir)
    ensure_dir(mc_modded_dir)
    ensure_dir(f'{mc_modded_dir}\mods')

    if not mc_version:
        mc_version = ask_version()
    elif mc_version == 'latest':
        mc_versions = get_mc_versions()
        mc_version = mc_versions[0]
    elif mc_version == 'snapshot':
        mc_versions = get_mc_versions()
        f = re.compile('\d.\d\d$')
        for version in mc_versions:
            if f.match(version):
                mc_version = version
                break
    
    if debug:
        mod_list = json.load(open('mods.json'))
    else:
        mod_list = json.loads(requests.get(mod_list_url).content)
    
    if not mod_ids:
        mod_names = ask_mods(mod_list, server)
        mod_ids = [mod['id'] for mod in mod_list if mod['name'] in mod_names]
    mod_ids = set(mod_ids)
    mod_ids.update(resolve_dependencies(mod_ids, mod_list))
    mods = [mod for mod in mod_list if mod['id'] in mod_ids]
    
    if not installer_path:
        log.print_log('Beginning setup: Downloading Fabric Installer', 'green')
        installer_path = download_fabric_installer(mc_dir)
        log.print_log('Finished Downloading Fabric Installer.', 'green')

    log.print_log('Starting Fabric Loader installation.', 'green')
    install_fabric(installer_path, mc_dir, mc_version, server)
    log.print_log('Finished Fabric Loader installation.', 'green')

    log.print_log('Starting mod installation. This may take a while...', 'green')
    delete_mods(mc_modded_dir)

    # Install Mods
    with click.progressbar( mods, 
                            label='Installing Mods',
                            show_percent=False,
                            show_pos=True,
                            fill_char=u'\u2588',
                            empty_char=' ',
                            color=colorama) as bar:
        for mod in bar:
            try:
                install_mod(mod, mc_modded_dir, mc_version)
            except ModVersionNotFoundError:
                log.queue_log(f'{mod["name"]} is not available for {mc_version}.', 'red')
                mods.remove(mod)
            except InvalidModResourceError:
                log.print_log(f'\nThe mod data for {mod["name"]} was invalid', 'red')
                mods.remove(mod)
            except Exception as e:
                log.print_log(f'\nAn unknown error was encountered while installing {mod["name"]}:', 'red')
                pprint(e)
                mods.remove(mod)
    
    log.print_queue()
    log.print_log(f'Successfully installed Fabric Loader and {len(mods)} mod(s) for Minecraft {mc_version}.', 'green')
    clean_exit('green')

if __name__ == '__main__':
    main()