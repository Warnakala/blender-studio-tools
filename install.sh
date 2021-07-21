#!/bin/bash

#check if pip3 is installed 
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 is not installed"
    
    #asl user to install pip
    while true; do
    read -p "Do you wish to install this program? (Yy/Nn)" yn
    case $yn in
        [Yy]* ) sudo apt install python3-pip; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done 
fi

#cd into directory of install.sh script 
dirpath=`dirname "$0"`
cd $dirpath

#build wheel 
python3 setup.py bdist_wheel

#install wheel with pip 
pip3 install dist/blender_purge-0.1.0-py2.py3-none-any.whl --user --force-reinstall

#log end 
printf "\nInstalled blender-purge. Type 'bpurge' in new console to start program!"
printf "\nTo uninstall type 'pip3 uninstall blender-purge'\n"
