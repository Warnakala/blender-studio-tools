# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation

import zipfile
import hashlib
import sys
import os
import subprocess
from pathlib import Path
from typing import List
import shutil
import argparse
import re
from typing import Pattern
import datetime

REPO_ROOT_DIR = Path(__file__).parent.parent.parent
# BORROWED FROM https://github.com/pawamoy/git-changelog/blob/master/src/git_changelog/commit.py
TYPES: dict[str, str] = {
    "add": "Added",
    "fix": "Fixed",
    "change": "Changed",
    "remove": "Removed",
    "merge": "Merged",
    "doc": "Documented",
    "breaking": "Breaking",
}


def parse_commit(commit_message: str) -> dict[str, str]:
    """
    Parse the type of the commit given its subject.
    Arguments:
        commit_subject: The commit message subject.
    Returns:
        Dict containing commit message and type
    """
    type = ""
    # Split at first colon to remove prefix from commit
    if ": " in commit_message:
        message_body = commit_message.split(': ')[1]
    else:
        message_body = commit_message
    type_regex: Pattern = re.compile(r"^(?P<type>(%s))" % "|".join(TYPES.keys()), re.I)
    breaking_regex: Pattern = re.compile(
        r"^break(s|ing changes?)?[ :].+$",
        re.I | re.MULTILINE,
    )

    type_match = type_regex.match(message_body)
    if type_match:
        type = TYPES.get(type_match.groupdict()["type"].lower(), "")
    if bool(breaking_regex.search(message_body)):
        type = "Breaking"
    return {
        "message": message_body,
        "type": type,
    }


parser = argparse.ArgumentParser()
parser.add_argument(
    "-m",
    "--msg",
    help="Find commit with this message and use it as the last version.",
    type=str,
)
parser.add_argument(
    "-n",
    "--name",
    help="Only update the addon corrisponding to this name(s).",
    type=str,
)

parser.add_argument(
    "-b",
    "--bump",
    help="Bump the major version number, otherwise bump minor version number",
    action="store_true",
)

parser.add_argument(
    "-f",
    "--force",
    help="Bump version even if no commits are found",
    action="store_true",
)


def cli_command(command: str) -> subprocess:
    """Run command in CLI and capture it's output
    Arguments:
        command: String of command to run in CLI.
    """
    output = subprocess.run(command.split(' '), capture_output=True, encoding="utf-8")
    return output


def exit_program(message: str):
    print(message)
    sys.exit(0)


def write_file(file_path: Path, content):
    file = open(file_path, 'w')
    file.writelines(content)
    file.close()


def get_directory(repo_root: Path, folder_name: str) -> Path:
    """Returns directory PATH, creates one if none exists"""
    path = repo_root.joinpath(folder_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def clean_str(string: str) -> str:
    """Returns string with qoutes and line breaks removed"""
    return string.replace('\n', '').replace("'", "").replace('"', '')


def generate_checksum(archive_path: str) -> str:
    """
    Generate a checksum for a zip file
    Arguments:
        archive_path: String of the archive's file path
    Returns:
        sha256 checksum for the provided archive as string
    """
    sha256 = hashlib.sha256()
    with open(archive_path, 'rb') as file:
        # Read the file in chunks to handle large files efficiently
        chunk = file.read(4096)
        while len(chunk) > 0:
            sha256.update(chunk)
            chunk = file.read(4096)
    return sha256.hexdigest()


def changelog_category_get(changelog_messages: dict[str, str], title: str, key: str):
    """
    Generate changelog messages for a specific category.
    Types are defined in global variable 'TYPES'
    Arguments:
        changelog_messages: dict contaning commit message & type
        title: Title of the changelog category
        key: Key for category/type as defined in global variable TYPES
    Returns:
        changelog entry for the given category/type as a string
    """
    entry = ''
    if not any(commit for commit in changelog_messages if commit["type"] == key):
        return entry
    entry += f"### {title} \n"
    for commit in changelog_messages:
        if commit["type"] == key:
            entry += f'- {commit["message"]}'
    entry += "\n"
    return entry


def changelog_generate(commit_hashes: list[str], version: str) -> str:
    """
    Generate Changelog Entries from a list of commits hashes
    Arguments:
        commit_hashes: A list of commit hashes to include in Changelog
        version: Latest addon version number
    Returns:
        complete changelog for latest version as string
    """

    log_entry = f'## {version} - {datetime.date.today()} \n \n'
    changelog_messages = []
    if commit_hashes is not None:
        for commit in commit_hashes:
            message = (
                f"{cli_command(f'git log --pretty=format:%s -n 1 {commit}').stdout}\n"
            )
            changelog_messages.append(parse_commit(message))

        for type in TYPES:
            log_entry += changelog_category_get(
                changelog_messages, TYPES.get(type).upper(), TYPES.get(type)
            )

        log_entry += "### UN-CATEGORIZED \n"
        for commit in changelog_messages:
            if commit["message"] not in log_entry:
                log_entry += f"- {commit['message']}"
    log_entry += "\n"
    return log_entry


def changelog_commits_get(directory: Path, commit_message: str) -> list[str]:
    """
    Get list of commit hashes, that affect a given directory
    Arguments:
        directory: Name of directory/folder to filter commits
        commit_message: Prefix of commit to use as base for latest release
    Returns:
        list of commit hashes
    """
    last_version_commit = None
    commits_in_folder = cli_command(
        f'git log --format=format:"%H" {directory}/*'
    ).stdout.split('\n')
    # Find Last Version
    for commit in commits_in_folder:
        commit = clean_str(commit)
        commit_msg = cli_command(f'git log --format=%B -n 1 {commit}')
        if commit_message in commit_msg.stdout:
            last_version_commit = commit
    if last_version_commit is None:
        return

    commits_since_release = cli_command(
        f'git rev-list {clean_str(last_version_commit)[0:9]}..HEAD'
    ).stdout.split('\n')
    commit_hashes = []

    for commit in commits_in_folder:
        if any(clean_str(commit) in x for x in commits_since_release):
            commit_hashes.append(clean_str(commit))
    return commit_hashes


def changelog_file_write(file_path: Path, content: str):
    """
    Append changelog to existing changelog file or create a new
    changelog file if none exists
    Arguments:
        file_path: PATH to changelog
        content: changelog for latest version as string
    """
    if file_path.exists():
        dummy_file = str(file_path._str) + '.bak'
        with open(file_path, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
            write_obj.write(content)
            for line in read_obj:
                write_obj.write(line)
        os.remove(file_path)
        os.rename(dummy_file, file_path)
    else:
        write_file(file_path, content)
    return file_path


def addon_package(directory: Path, commit_prefix: str, is_major=False, force=False):
    """
    For a give directory, if new commits are found after the commit matching 'commit_prefix',
     bump addon version, generate a changelog, commit changes and package addon into an archive.
     Print statements indicate if addon was version bumped, or if new version was found.
    Arguments:
        directory: Name of directory/folder to filter commits
        commit_prefix: Prefix of commit to use as base for latest release
        is_major: if major 2nd digit in version is updated, else 3rd digit
    """
    commit_msg = 'Version Bump:' if commit_prefix is None else commit_prefix
    commits_in_folder = changelog_commits_get(directory, commit_msg)
    dist_dir = get_directory(REPO_ROOT_DIR, "dist")
    if commits_in_folder or force:
        init_file, version = addon_version_bump(directory, is_major)
        change_log = changelog_generate(commits_in_folder, version)
        change_log_file = changelog_file_write(
            directory.joinpath("CHANGELOG.MD"), change_log
        )
        cli_command(f'git reset')
        cli_command(f'git stage {change_log_file}')
        cli_command(f'git stage {init_file}')
        subprocess.run(
            ['git', 'commit', '-m', f"Version Bump: {directory.name} {version}"],
            capture_output=True,
            encoding="utf-8",
        )
        print(f"Version Bump: {directory.name} {version}")
        name = directory.name
        addon_output_dir = get_directory(dist_dir, directory.name)

        zipped_addon = shutil.make_archive(
            addon_output_dir.joinpath(f"{name}_{version}"), 'zip', directory
        )
        checksum = generate_checksum(zipped_addon)
        checksum_file = write_file(
            addon_output_dir.joinpath(f"{name}_{version}.sha256"),
            f"{checksum} {name}_{version}.zip",
        )
    else:
        print(f"No New Version: {directory.name}")


def addon_version_get(version_line: str, is_major: bool) -> str:
    """
    Read bl_info within addon's __init__.py file to get new version number
    Arguments:
        version_line: Line of bl_info containing version number
        is_major: if major 2nd digit in version is updated, else 3rd digit
    Returns
        Latest addon version number
    """
    version = version_line.split('(')[1].split(')')[0]
    # Bump either last digit for minor versions and second last digit for major
    if is_major:
        new_version = version[:-4] + str(int(version[3]) + 1) + version[-3:]
    else:
        new_version = version[:-1] + str(int(version[-1]) + 1)
    return new_version


def addon_version_bump(directory: Path, is_major: bool):
    """
    Update bl_info within addon's __init__.py file to indicate
    version bump. Expects line to read as '"version": (n, n, n),\n'
    Arguments:
        directory: Name of directory/folder containing addon
        is_major: if major 2nd digit in version is updated, else 3rd digit

    Returns:
        init_file: PATH to init file that has been updated with new version
        version: Latest addon version number
    """

    version_line = None
    str_find = "version"
    init_file = directory.joinpath("__init__.py")
    with open(init_file, 'r') as myFile:
        for num, line in enumerate(myFile):
            if str_find in line and "(" in line and line[0] != "#":
                version_line = num
                break  # Use first line found

    file = open(
        init_file,
    )
    lines = file.readlines()
    version = addon_version_get(lines[version_line], is_major)
    repl_str = f'    "version": ({version}),\n'
    lines[version_line] = repl_str
    out = open(init_file, 'w')
    out.writelines(lines)
    out.close()
    return init_file, version.replace(', ', '.').replace(',', '.')


def main() -> int:
    args = parser.parse_args()
    msg = args.msg
    bump = args.bump
    user_names = args.name
    force = args.force
    addon_folder = REPO_ROOT_DIR.joinpath(REPO_ROOT_DIR, "scripts-blender/addons")
    addon_dirs = [
        name
        for name in os.listdir(addon_folder)
        if os.path.isdir(addon_folder.joinpath(name))
    ]
    if user_names:
        addon_dirs = [
            name
            for name in os.listdir(addon_folder)
            if os.path.isdir(addon_folder.joinpath(name)) and name in user_names
        ]
    for dir in addon_dirs:
        addon_to_package = addon_folder.joinpath(addon_folder, dir)
        addon_package(addon_to_package, msg, bump, force)
    return 0


if __name__ == "__main__":
    main()
