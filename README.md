# blender-kitsu
blender-kitsu is a Blender addon to interact with Kitsu from within Blender. It also has features that are not directly realted to Kitsu but support certain aspects of the Blender Studio Pipeline.

## Installation
Download or clone this repository.
In the root project folder you will find the 'blender_kitsu' folder. Place this folder in your Blender addons directory or create a sym link to it.

## How to get started
After installing you need to setup the addon preferences to fit your environment.
In order to be able to log in to Kitsu you need a server that runs the Kitsu production management suite.
Information on how to set up Kitsu can be found [here](https://zou.cg-wire.com/).

If Kitsu is up and running and you can succesfully log in via the web interface you have to setup the addon preferences.

> **_NOTE:_**  If you want to get started quickly you only need to setup: step1, step2

1. **Setup login data**

![image info](./docs/images/prefs_login.jpg)

| | |
| ------ | ------ |
| **Host** | The webadress of your kitsu server (e.G https://kitsu.mydomain.com) |
| **Email** | The email you use to log in to kitsu |
| **Password** | The password you use to log in to kitsu |

Press the login button. If the login was succesfull, the next step is..

2. **Select active project from the dropdown menu and setup project settings**

![image info](./docs/images/prefs_project.jpg)

| | |
| ------ | ------  |
| **Project Root Directory** | Path to the root of your project. Will later be used to configurate the addon on a per project basis. |

3. **Setup animation tools**

![image info](./docs/images/prefs_anim_tools.jpg)

| | |
| ------ | ------  |
| **Project Root Directory** | Path to the root of your project. Will later be used to configurate the addon on a per project basis. |
| **Playblast Root Directory** | Path to a directory in which playblasts will be saved to. |
| **Open Webbrowser after Playblast** | Open default browser after playblast which points to shot on kitsu |

4. **Setup lookdev tools**

![image info](./docs/images/prefs_lookdev.jpg)

| | |
| ------ | ------  |
| **Render Presets Directory** | Path to a directory in which you can save .py files that will be displayed in render preset dropdown. More info in: How to use render presets.|

5. **Setup media search paths**

![image info](./docs/images/prefs_outdated_media.jpg)

| | |
| ------ | ------  |
| **Path List**| List of paths to top level directorys. Only media that is a child (recursive) of one of these directories will be scanned for outdated media.|

6. **Setup Miscellaneous settings**

![image info](./docs/images/prefs_misc.jpg)

| | |
| ------ | ------  |
| **Thumbnail Directory**| Directory where thumbnails will be saved before uploading them to kitsu. Cannot be edited.|
| **Sequence Editor Render Directory** | Directory where sequence editor renderings will be saved before uploading them to kitsu. Cannot be edited.|
| **Enable Debug Operators**| Enables extra debug operators in the sequence editors Kitsu tab.|
| **Advanced Settings**| Advanced settings that changes how certain operators work. Will be discussed in detail here:|

After setting up the addon preferences you can make use of all the features of blender-kitsu
## Features
blender-kitsu has many feature and in this documentation they are divided in different sections.

#### Sequence Editor
blender-kitsu sequence editor tools were constructed with the idea in mind to have a relationship between sequence strips and shots on Kitsu. This connection enables the exchange of metadata between the edit and the shots on Kitsu. Some examples are frame ranges of shots can be directly updated from the edit or thumbnails can be rendered and uploaded to Kitsu with a click of a button and many more which you will find out in this section:

##### Metastrips
Metastrips are regular Movie Strips that can be linked to a shot in kitsu. It is a good idea to create a seperate meta strip in a seperate channel that represents the shot. That gives you the freedom to assemble a shot out of multiple elements, like multiple storyboard pictures, and still have one metastrip that contains the full shot range.

![image info](./docs/images/metastrip.001.jpg)

###### Create a metastrip
1. Select a sequence strip for which you want to create a metastrip and execute the `Create Metastrip` operator.
This will import a metastrip.mp4 (1000 frame black video) file which is saved in the addons repository. The metastrip will be placed one channel above the selected strips. Make sure there is enough space otherwise the metastrip will not be created.

###### Initialize/Link a shot
1. Select a metastrip and open the `Kitsu` tab in the sidebar of the sequence editor. You will find multiple ways on how to initialize your strip.
![image info](./docs/images/sqe_init_shot.jpg)

2. Case A: Shot does **already exists** on Kitsu
    2.1 Execute the `Link Shot` operator and a pop up will appear that lets you select the sequence and the shot to link to
    2.2 Alternatively you can also link a shot by pasting the URL. (e.G: https://kitsu.yourdomain.com/productions/fc77c0b9-bb76-41c3-b843-c9b156f9b3ec/shots/e7e6be02-5574-4764-9077-965d57b1ec12)
![image info](./docs/images/sqe_link_shot.jpg)

3. Case B: Shot **does not exist** on Kitsu yet
    3.1 Execute the `Initialize Shot` Operator.
    3.2 Link this strip to a sequence with the `Link Sequence` operator or create a new seuence with the `Submit New Sequence` operator.
    3.3 Type in the name of the new shot in the `Shot` field
    3.4 Execute the `Submit New Shot` operator in the `Push` Panel (Will warn you if the shot already exists on Kitsu)

If you select a single linked strip you will see a `Metadata` panel that shows you the information that is related to the sequence and shot the strip is linking to.

![image info](./docs/images/sqe_metadata.jpg)

## Troubleshoot
blender-kitsu makes good use of logging and status reports. Most of the operators report information in the blender info bar. More detailed logs can be found in the blender system console. If you feel like anything went wrong, consider opening a console and check the logs.

## Plugins
---
This project uses gazu as a submodule to interact with the gazu data base.
- gazu doc : https://gazu.cg-wire.com/
- dazu repo: https://github.com/cgwire/gazu

## Development
---
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your blender addons directory to the blender_kitsu folder.
