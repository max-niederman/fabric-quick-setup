import mods
import json
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

def log(string, color, font='slant', figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

def fabric(mc_dir, mc_version):
    subprocess.call(['java', 
        '-jar', 
        'fabric-installer.jar', 
        'client',
        '-snapshot',
        '-mcversion',
        mc_version,
        '-dir',
        mc_dir,
        ])

def ask_mc_dirs():
    questions = [
        {
            'type': 'input',
            'name': 'mc_dir',
            'message': 'Enter Minecraft Directory',
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
@click.option('--mc-dir', help='Minecraft directory')
@click.option('--mc-modded-dir', help='Minecraft modded directory')
@click.option('--version', help='Minecraft version to install')
@click.option('--mods', multiple=True, help='The person to greet.')
def main(mc_dir, mc_modded_dir, version, mods):
    """
    CLI to install Fabric Loader and Popular Mods
    """
    log('Fabric Quick Setup', color='blue', figlet=True)
    log('Welcome to Fabric Quick Setup', 'green')

    if not mc_dir:
        mc_dirs = ask_mc_dirs()
        mc_dir, mc_modded_dir = mc_dirs['mc_dir'], mc_dirs['mc_modded_dir']

    if not version:
        version = ask_version()
    
    if not mods:
        mod_list = json.load(open('mods.json'))
        mod_names = ask_mods(mod_list)
        mods = [mod for mod in mod_list if mod['name'] in mod_names]
    
    log('Beginning setup: Installing Fabric Loader', 'green')

    fabric(mc_dir, version)

if __name__ == '__main__':
    main()