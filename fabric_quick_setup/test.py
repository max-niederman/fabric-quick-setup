import subprocess
installer = subprocess.run(['java', 
            '-jar', 
            'fabric-installer.jar', 
            'server',
            '-snapshot',
            '-mcversion',
            '20w20b',
            '-dir',
            'F:/test',
            ])