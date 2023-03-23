#!/bin/bash
# This script can be used to quickly package the content of the project folder
# in to a zip file. It will append the version string at the end.
# Before packaging it will remove all __pycache__ folders.
# Useful for uploading it as a static asset on studio.blender.org

# Grab project version with poetry.
VERSION=$(poetry version -s)

# Read name value out of pyproject.toml file.
NAME=$(sed -n "s/name = //p" pyproject.toml | sed 's/"//g')

# Generate project slug by replacing - in name with _
SLUG=$(echo $NAME | sed 's/-/_/g')

# Generate outputpath for zip.
OUTPUT_PATH="dist/$NAME-$VERSION"

# Remove all __pycache__ folder in project directory.
DIRS_REMOVE=$(find $SLUG -name __pycache__ -type d)
if [ -n "${DIRS_REMOVE}" ]
then
    echo "Remove __pycache__ folders"
    echo $DIRS_REMOVE
    find $SLUG -name __pycache__ -type d -print0 | xargs -0 rm -r --
    echo
fi

# Create dist folder.
if ! [[ -d "dist" ]]
then
    mkdir -p "dist"
fi

# Zip it all up.
zip -r $OUTPUT_PATH.zip $SLUG

echo
echo "Zipped $SLUG to $OUTPUT_PATH"
