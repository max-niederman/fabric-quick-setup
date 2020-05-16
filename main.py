# Main.py
from mod import *
import json
import os
import subprocess
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
    log(f'Starting mod installation: {mod_dict["name"]}', 'green')
    mod = Mod(mod_dict['resource'])
    try:
        mod.install(mc_modded_dir, mc_version)
        log(f'Finished mod installation: {mod_dict["name"]}', 'green')
    except ModVersionNotFoundError:
        if 'alternative' in mod_dict['resource']:
            questions = [
                {
                    'type': 'confirm',
                    'message': f'{mod_dict["name"]} is not available for {mc_version}. Should I try installing {mod_dict["resource"]["alternative"]["name"]} instead? Y/n',
                    'name': 'install',
                    'default': True,
                }
            ]
            answers = prompt(questions, style=style)
            if answers['install']:
                install_mod(mod_dict['resource']['alternative'], mc_modded_dir, mc_version)

def log(string, color, font='slant', figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

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

def ask_version():
    questions = [
        {
            'type': 'input',
            'name': 'version',
            'message': 'Enter Minecraft Version',
        }
    ]
    answers = prompt(questions, style=style)
    return answers['version']

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
@click.option('-d', '--mc-dir', type=click.Path(), help='Minecraft directory')
@click.option('-t', '--mc-modded-dir', type=click.Path(), help='Minecraft modded directory')
@click.option('-v', '--version', 'mc_version', help='Minecraft version to install')
@click.option('-m', '--mods', 'mod_ids', multiple=True, help='The person to greet.')
def main(appdata_path, mc_dir, mc_modded_dir, mc_version, mod_ids):
    """
    CLI to install Fabric Loader and Popular Mods
    """
    log('Fabric Quick Setup', color='blue', figlet=True)
    log('Welcome to Fabric Quick Setup', 'green')

    if not mc_dir:
        mc_dirs = ask_mc_dirs(appdata_path)
        mc_dir, mc_modded_dir = mc_dirs['mc_dir'], mc_dirs['mc_modded_dir']

    if not mc_version:
        # TODO: Automatically get latest snapshot as default value
        mc_version = ask_version()
    
    mod_list = json.load(open('mods.json'))
    if mod_ids:
        mods = [mod for mod in mod_list if mod['id'] in mod_ids]
    else:
        mod_names = ask_mods(mod_list)
        mods = [mod for mod in mod_list if mod['name'] in mod_names]
    
    log('Beginning setup: Installing Fabric Loader', 'green')
    
    # TODO: Progress bar
    fabric(mc_dir, mc_version)
    log('Finished Fabric Loader installation.', 'green')

    log('Removing old mods', 'green')
    delete_mods(mc_modded_dir)

    # TODO: Progress bar or checklist rather than message spam
    for mod in mods:
        try:
            install_mod(mod, mc_modded_dir, mc_version)
        except InvalidModResourceError:
            log(f'The mod data for {mod["name"]} was invalid', 'red')
            mods.remove(mod)
        except Exception as e:
            log(f'An unknown error was encountered while installing {mod["name"]}:', 'red')
            pprint(e)
            mods.remove(mod)
        
        
    log(f'Successfully installed Fabric Loader and {len(mods)} mod(s) for Minecraft {mc_version}.', 'green')

if __name__ == '__main__':
    main()