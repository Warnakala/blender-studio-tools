# Install instructions for the studio systems

If you are installing the whole system from scratch you need to first to do three things:

1. Setup a place where the iPXE boot loader can access files.
2. Install the iPXE loader onto a USB stick
3. Install the build server.

After this is done, you can start rolling out the system to the client computers.

## Installing the build server server

1. Boot from the iPXE payload on the USB stick. If it is has booted correctly you should be greeted by the following screen:
![IPXE Menu](/media/td-guide/gentoo-server/gentoo_server_ipxe.png)    
    
2. Select the second option “Boot Gentoo build server installer”
3. It will ask you to select keyboard layout, press enter if you want to use the default US layout when using the installer. (Or wait a few seconds and it will proceed with the US layout) ![Select Keyboard Layout](/media/td-guide/gentoo-server/gentoo_server_keyboard.png)
    
4. When it has successfully booted, it will automatically start the installer. You will only need to manually setup two things:

    a. The hostname of the computer (NOTE: This should be unique as some scripts relies on the hostname to provide status reports)![Hostname](/media/td-guide/gentoo-server/gentoo_server_set_hostname.png)
    
    
    b. Where you want the system to be installed and if you want to setup any additional storage drives 

    ![Active Drive](/media/td-guide/gentoo-server/gentoo_server_active_drive.png)
        
    _The “r” symbol denotes which disk will be formatted as the root drive._

    _The “+” symbol denotes which disk(s) will be formatted as storage drives._
        

::: info  Installation Duration
When these steps are complete, one simply has to wait for the installer to finish. It will download and compile all necessary programs and libraries for the standard Blender workstation needs. This will usually take a while. Unless you have a very fast and recent CPU, it is not unusual for it to take 6+ hours to complete When it is done it will ask you to press any key to reboot.
:::



## Installing client workstation 
Installing the client computers is **almost** exactly the same as installing the server. The only difference is that you should select the first option “Boot Gentoo installer (Blender Institute Customized)” in the iPXE boot menu.

It will pull all programs and libraries from the build server.

This is much faster than the server install process. On a **recent** workstation computer, the installation should complete in 15-20 minutes. On the more low powered computers in the office (the Intel NUCs for example), this will take around one hour or so.

As with the server, once the installation is complete, it will ask to press any key to reboot.Everything should have been set up and configured, no additional configuration should be required.