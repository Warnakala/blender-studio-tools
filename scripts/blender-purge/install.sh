#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color.

# Check if pip3 is installed.
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 is not installed"

    # Ask user to install pip.
    while true; do
    read -p "Do you wish to install this program? (Yy/Nn)" yn
    case $yn in
        [Yy]* ) sudo apt install python3-pip; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
fi

# Cd into directory of install.sh script.
dirpath=`dirname "$0"`
cd $dirpath

# Build wheel.
python3 setup.py bdist_wheel

# Install wheel with pip.
pip3 install dist/blender_purge-0.1.0-py2.py3-none-any.whl --user --force-reinstall

# Check if PATH variable is correct.
if ! [[ ":$PATH:" == *":$HOME/.local/lib/python3.8/site-packages:"* ]]; then
    printf "\n${RED}\$HOME/.local/lib/python3.8/site-packages is missing in PATH variable\n"
    printf "Please add 'export PATH=\"\$PATH:$HOME/.local/lib/python3.8/site-packages\"' to the file: \$HOME/.profile${NC}\n"
fi

if ! [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    printf "\n${RED}\$HOME/.local/bin is missing in PATH variable\n"
    printf "Please add 'export PATH=\"\$PATH:$HOME/.local/bin\"' to the file: \$HOME/.profile${NC}\n"
fi

# Log end.
printf "\n${GREEN}Installed blender-purge. Type 'bpurge' in console to start program!\n"
printf "To uninstall type 'pip3 uninstall blender-purge'${NC}\n"
