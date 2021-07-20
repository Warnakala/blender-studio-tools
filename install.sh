#!/bin/bash
dirpath=`dirname "$0"`
cd $dirpath

python3 setup.py bdist_wheel


