
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator
from ..threaded.background_process import Processes

class SVN_OT_custom_tooltip(Operator):
    """Tooltip"""
    bl_idname = "svn.custom_tooltip"
    bl_label = ""
    bl_description = " "
    bl_options = {'INTERNAL'}

    tooltip: StringProperty(
        name="Tooltip",
        description="Tooltip that is displayed when mouse hovering this operator"
    )
    copy_on_click: BoolProperty(
        name="Copy on Click",
        description="If True, the tooltip will be copied to the clipboard when the operator is clicked",
        default=False
    )

    @classmethod
    def description(cls, context, properties):
        tooltip = properties.tooltip
        if properties.copy_on_click:
            tooltip = "Copy to clipboard: " + properties.tooltip
        return tooltip

    def execute(self, context):
        if self.copy_on_click:
            context.window_manager.clipboard = self.tooltip
            self.report({'INFO'}, "Copied to Clipboard: " + self.tooltip)
        return {'FINISHED'}


class SVN_OT_clear_error(Operator):
    bl_idname = "svn.clear_error"
    bl_label = "Error:"
    bl_description = ""
    bl_options = {'INTERNAL'}

    process_id: StringProperty()

    @classmethod
    def description(cls, context, properties):
        process = Processes.get(properties.process_id)
        if not process:
            return "Process doesn't exist: " + properties.process_id
        return process.error_description + "\n\n" + process.error + "\n\n Click to clear the error and copy it to your clipboard"

    def execute(self, context):
        process = Processes.get(self.process_id)
        if not process:
            self.report({'WARNING'}, f'Process not found: "{self.process_id}"')
            return {'FINISHED'}
        context.window_manager.clipboard = process.error_description + "\n\n" + process.error

        if process.repeat_delay > 0:
            process.start()
        else:
            process.error = ""
            process.output = ""

        self.report({'INFO'}, "Copied error to Clipboard.")

        return {'FINISHED'}


registry = [
    SVN_OT_custom_tooltip,
    SVN_OT_clear_error
]