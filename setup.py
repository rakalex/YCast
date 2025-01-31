from setuptools import setup, find_packages

import ycast

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='ycast',
    version=ycast.__version__,
    author='rakalex',
    author_email='rak.alexei@gmail.com',
    description='Self hosted vTuner internet radio service emulation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,    
    url='https://github.com/rakalex/YCast',
    entry_points={"console_scripts": ["ycast=ycast.__main__:launch_server"]},
    license='GPLv3',
    classifiers=[
        'Development Status ::Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=[
        'ycast',
        'streaming',
        'vtuner',
        'internet radio',
        'music',
        'radio',
        'shoutcast',
        'avr',
        'emulation',
        'yamaha',
        'onkyo',
        'denon'
    ],
    install_requires=['Pillow', 'Flask'],
    packages=find_packages(exclude=['contrib', 'docs', 'tests'])
)
