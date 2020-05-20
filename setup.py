import setuptools

def readme():
    with open('README.md') as f:
        return f.read()

setuptools.setup(
    name='fabric-quick-setup',
    version='0.1.4',
    description='CLI to quickly and easily install Fabric Loader and Popular Minecraft Mods',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='http://github.com/max-niederman/fabric-quick-setup',
    author='Max Niederman',
    author_email='maxniederman@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    entry_points = {
        'console_scripts': ['fabric-quick-setup=fabric_quick_setup.cli:main']
    })