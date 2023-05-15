from .background_process import BackgroundProcess

class BGP_SVN_Activate_File(BackgroundProcess):
    """This crazy hacky method of activating the file with some delay is necessary 
    because Blender won't let us select the file immediately when changing the 
    directory - some time needs to pass before the files actually appear.
    (This is visible with the naked eye as the file browser is empty for a 
    brief moment whenever params.dictionary is changed.)
    """

    name = "Activate File"
    needs_authentication = False
    tick_delay = 0.1
    debug = False

    def acquire_output(self, context, prefs):
        self.output = "dummy"

    def process_output(self, context, prefs):
        if not hasattr(context.scene, 'svn'):
            return

        repo = context.scene.svn.get_repo(context)
        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.spaces.active.activate_file_by_relative_path(
                    relative_path=repo.active_file.name)

        self.stop()

    def get_ui_message(self, context):
        return ""
