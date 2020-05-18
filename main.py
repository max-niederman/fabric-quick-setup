# Main.py
from mod import *
import json
import os
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

def fabric(mc_dir, mc_version): 
    subprocess.run(['java', 
        '-jar', 
        'fabric-installer.jar', 
        'client',
        '-snapshot',
        '-noprofile',
        '-mcversion',
        mc_version,
        '-dir',
        mc_dir,
        ],
        stdout=subprocess.DEVNULL)

def delete_mods(mc_dir):
    mod_dir = f'{mc_dir}\\mods'
    files = [f for f in os.listdir(mod_dir)]
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
        dependencies.update(mod['dependencies'])
    return dependencies

def ask_mc_dirs(appdata_path):
    questions = [
        {
            'type': 'input',
            'name': 'mc_dir',
            'message': 'Enter Minecraft Directory',
            'default': lambda answers : f'{appdata_path}\\.minecraft'
        },
        {
            'type': 'input',
            'name': 'mc_modded_dir',
            'message': 'Enter Modded Minecraft Directory.',
            'default': lambda answers : answers['mc_dir']
        }
    ]
    answers = prompt(questions, style=style)
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

# TODO: Hidden mods in list
def ask_mods(mods):
    questions = {
        'type': 'checkbox',
        'message': 'Select Mods to Install',
        'name': 'mods',
        'choices': [{ 'name': mod['name'] } for mod in mods],
    }
    answers = prompt(questions)
    return answers['mods']

@click.command()
@click.option('--appdata-path', type=click.Path(), envvar='APPDATA')
@click.option('--debug', is_flag=True, default=False)
@click.option('-u', '--mod-list', 'mod_list_url', default='https://raw.githubusercontent.com/max-niederman/fabric-setup/master/mods.json?token=AEVMMKTTLQNJ7F5VGSNJYSS6ZKOBK', type=str, help='Mod list URL.')
@click.option('-d', '--mc-dir', type=click.Path(), help='Minecraft directory')
@click.option('-t', '--mc-modded-dir', type=click.Path(), help='Minecraft modded directory')
@click.option('-v', '--version', 'mc_version', type=str, help='Minecraft version to install')
@click.option('-m', '--mods', 'mod_ids', type=str, multiple=True, help='The person to greet.')
def main(appdata_path, debug, mod_list_url, mc_dir, mc_modded_dir, mc_version, mod_ids):
    """
    CLI to install Fabric Loader and Popular Mods
    """
    log.print_log('Fabric Quick Setup', 'blue', figlet=True)
    log.print_log('Welcome to Fabric Quick Setup', 'green')

    if not mc_dir:
        mc_dirs = ask_mc_dirs(appdata_path)
        mc_dir, mc_modded_dir = mc_dirs['mc_dir'], mc_dirs['mc_modded_dir']

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
        mod_list = requests.get(mod_list_url).json()
    
    if not mod_ids:
        mod_names = ask_mods(mod_list)
        mod_ids = [mod['id'] for mod in mod_list if mod['name'] in mod_names]
    mod_ids = set(mod_ids)
    mod_ids.update(resolve_dependencies(mod_ids, mod_list))
    mods = [mod for mod in mod_list if mod['id'] in mod_ids]
    
    log.print_log('Beginning setup: Installing Fabric Loader', 'green')
    
    # TODO: Informative output
    fabric(mc_dir, mc_version)
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

if __name__ == '__main__':
    try:
        main()
    except KeyError:
        log.print_log('KeyError detected. Exiting...', 'red')