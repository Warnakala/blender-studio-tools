# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

import bpy
import threading
import random
from typing import List

from ..util import get_addon_prefs, redraw_viewport
from bpy.app.handlers import persistent


def get_recursive_subclasses(typ) -> List[type]:
    ret = []
    for subcl in typ.__subclasses__():
        ret.append(subcl)
        ret.extend(get_recursive_subclasses(subcl))
    return ret

class Processes:
    processes = {}

    @classmethod
    def get(cls, proc_name: str):
        """Return a process if it exists, or None."""
        return cls.processes.get(proc_name, None)

    @classmethod
    def start(cls, proc_name: str, **kwargs):
        """Start a process if it's stopped, or create it if it hasn't yet been instantiated."""
        process = cls.get(proc_name)
        if process:
            process.start()
            return
        else:
            for subcl in get_recursive_subclasses(BackgroundProcess):
                if subcl.name == proc_name:
                    cls.processes[subcl.name] = subcl(**kwargs)
                    return

        raise Exception("SVN: Process name not found: ", proc_name)

    @classmethod
    def stop(cls, proc_name: str):
        """Stop a process if it exists, otherwise do nothing."""
        process = cls.get(proc_name)
        if process:
            process.stop()

    @classmethod
    def kill(cls, proc_name: str):
        """Destroy a process entirely, such that it cannot be started again
        without initializing a new instance."""
        process = cls.get(proc_name)
        if process:
            process.stop()
            del cls.processes[proc_name]


class BackgroundProcess:
    """
    Base class that uses bpy.app.timers and threading to execute SVN commands 
    without freezing the interface.

    The class should be extended and the process_output and acquire_output functions 
    implemented for each SVN command, then a single instance of that subclass should 
    be created, which can from that point on be used to manage that SVN process.
    """

    name = "Unnamed Process"

    # If the acquire_output() function doesn't write anything into
    # self.output/self.error after this long, we will write a timeout
    # error into self.error.
    timeout = 10

    # After a successful execution of process_output(), wait this many seconds
    # before trying to acquire_output() again.
    # If 0, repeated execution will stop.
    repeat_delay = 15

    # How many seconds to wait between checks for whether output has been acquired yet.
    tick_delay = 1.0

    # Time in seconds to delay the first execution by.
    first_interval = 0

    needs_authentication = False

    # Displayed in the tooltip on mouse-hover in the error message when an error occurs.
    error_description = "SVN Error:"

    debug = False

    def debug_print(self, msg: str):
        if self.debug:
            print(f"{self.name} (#{self.id}): {msg}")

    def __init__(self):
        self.thread = None
        self.thread_start_time = 0

        self.is_running = False
        self.output = ""
        self.error = ""
        self.id = int(random.random() * 10000)

        self.start()

    def acquire_output(self, context, prefs):
        """
        Executed from a thread to avoid UI freezing during execute_svn_command().

        Should save data into self.output and self.error.
        Reading Blender data from this function is safe, but writing isn't!
        """
        raise NotImplementedError

    def process_output(self, context, prefs):
        """
        Executed on main thread when there is any value in self.output or self.error.

        It is safe to read and write Blender data from this function.
        """
        raise NotImplementedError

    def tick(self, context, prefs):
        """
        Executed repeatedly while the timer is running, with tick_delay seconds between
        each call.

        Doesn't have to be used for anything. Can be useful for redrawing the UI. 
        Just be careful with this though.
        """
        return

    @persistent
    def timer_function(self):
        """This is the actual function registered to bpy.app.timers."""
        context = bpy.context
        repo = context.scene.svn.get_repo(context)
        if not repo:
            self.debug_print("Shutdown: Not in repo.")
            self.is_running = False
            return

        prefs = get_addon_prefs(context)

        self.tick(context, prefs)
        if not self.is_running:
            # Since unregistering timers seems to be broken, let's allow setting
            # is_running to False in order to shut down this process.
            self.debug_print("Shutdown: is_running was set to False.")
            return

        if self.needs_authentication and not repo.authenticated:
                self.debug_print("Shutdown: Authentication needed.")
                self.is_running = False
                return

        if not self.thread or not self.thread.is_alive() and not self.output and not self.error:
            self.thread = threading.Thread(
                target=self.acquire_output, args=(context, prefs))
            self.thread.start()
            self.debug_print("Started thread")
            return self.tick_delay
        elif self.error:
            self.debug_print("Shutdown: There was an error.")
            self.is_running = False
            return
        elif self.output:
            self.debug_print("Processing output: \n" + str(self.output))
            self.process_output(context, prefs)
            self.output = ""
            redraw_viewport()
            if self.repeat_delay == 0:
                self.debug_print(
                    "Shutdown: Output was processed, repeat_delay==0.")
                self.is_running = False
                return
            self.debug_print(f"Processed output. Waiting {self.repeat_delay}")
            return self.repeat_delay
        elif not self.thread and not self.thread.is_alive() and self.repeat_delay == 0:
            self.debug_print("Shutdown: Finished.\n")
            self.is_running = False
            return

        self.debug_print(f"Tick delay: {self.tick_delay}")

        return self.tick_delay

    def get_ui_message(self, context) -> str:
        """Return a string that should be drawn in the UI for user feedback, 
        depending on the state of the process."""

        if self.is_running:
            return "Running..."
        return ""

    def clear_error(self):
        """Sub-classes should override this function to define behaviour on how to handle their errors."""
        self.error = ""
        self.output = ""

        self.stop()

        if self.repeat_delay > 0:
            self.start()

    def start(self, persistent=True):
        """Start the process if it isn't running already, by registering its timer function."""
        self.is_running = True
        if not bpy.app.timers.is_registered(self.timer_function):
            self.debug_print("Register timer")
            bpy.app.timers.register(
                self.timer_function, 
                first_interval=self.first_interval, 
                persistent=persistent
            )

    def stop(self):
        """Stop the process if it isn't running, by unregistering its timer function"""
        self.is_running = False
        if bpy.app.timers.is_registered(self.timer_function):
            # This won't work if the timer has returned None at any point, as that
            # will have already unregistered it.

            # Actually, it doesn't seem to work anyways...
            bpy.app.timers.unregister(self.timer_function)
            self.debug_print("Force-unregistered.")
