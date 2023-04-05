# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import pathlib
from typing import *
import bpy
from blender_kitsu.shot_builder.shot import ShotRef
from blender_kitsu.shot_builder.project import ensure_loaded_production, get_active_production
from blender_kitsu.shot_builder.builder import ShotBuilder
from blender_kitsu.shot_builder.task_type import TaskType
from blender_kitsu import prefs, cache, gazu
from blender_kitsu.shot_builder.anim_setup.core import  animation_workspace_delete_others, animation_workspace_vse_area_add
from blender_kitsu.shot_builder.editorial.core import editorial_export_get_latest
from blender_kitsu.shot_builder.builder.save_file import save_shot_builder_file


_production_task_type_items: List[Tuple[str, str, str]] = []

def production_task_type_items(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global _production_task_type_items
    return _production_task_type_items

_production_seq_id_items: List[Tuple[str, str, str]] = []

def production_seq_id_items(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global _production_seq_id_items
    return _production_seq_id_items

_production_shots: List[ShotRef] = []

def production_shots(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global _production_shots
    return _production_shots

_production_shot_id_items_for_seq: List[Tuple[str, str, str]] = []

def production_shot_id_items_for_seq(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global _production_shot_id_items_for_seq
    global _production_shot_id_items

    if not self.seq_id or not _production_shots:
        return []

    shots_for_seq: List[Tuple(str, str, str)] = [
        (s.name, s.name, "") for s in _production_shots
        if s.sequence.name == self.seq_id
        ]

    _production_shot_id_items_for_seq.clear()
    _production_shot_id_items_for_seq.extend(shots_for_seq)

    return _production_shot_id_items_for_seq

def reset_shot_id_enum(self : Any, context: bpy.types.Context) -> None:
    production_shot_id_items_for_seq(self, context)
    global _production_shot_id_items_for_seq
    if _production_shot_id_items_for_seq:
        self.shot_id = _production_shot_id_items_for_seq[0][0]

class SHOTBUILDER_OT_NewShotFile(bpy.types.Operator):
    """Build a new shot file"""
    bl_idname = "shotbuilder.new_shot_file"
    bl_label = "New Production Shot File"

    _timer = None
    _built_shot = False
    _add_vse_area = False
    _file_path = ''

    production_root: bpy.props.StringProperty(  # type: ignore
        name="Production Root",
        description="Root of the production",
        subtype='DIR_PATH')

    production_name: bpy.props.StringProperty(  # type: ignore
        name="Production",
        description="Name of the production to create a shot file for",
        options=set()
    )

    seq_id: bpy.props.EnumProperty(  # type: ignore
        name="Sequence ID",
        description="Sequence ID of the shot to build",
        items=production_seq_id_items,
        update=reset_shot_id_enum,
    )

    shot_id: bpy.props.EnumProperty(  # type: ignore
        name="Shot ID",
        description="Shot ID of the shot to build",
        items=production_shot_id_items_for_seq,
    )

    task_type: bpy.props.EnumProperty(  # type: ignore
        name="Task",
        description="Task to create the shot file for",
        items=production_task_type_items
    )
    auto_save: bpy.props.BoolProperty(
        name="Save after building.",
        description="Automatically save build file after 'Shot Builder' is complete.",
        default=True,
    )

    def modal(self, context, event):

        if event.type == 'TIMER' and not self._add_vse_area:
            # Show Storyboard/Animatic from VSE
            """Running as Modal Event because functions within execute() function like
            animation_workspace_delete_others() changed UI context that needs to be refreshed.
            https://docs.blender.org/api/current/info_gotcha.html#no-updates-after-changing-ui-context"""
            animation_workspace_vse_area_add(context) 
            self._add_vse_area = True

        if self._built_shot and self._add_vse_area:
            if self.auto_save:
                file_path = pathlib.Path()
                try:
                    save_shot_builder_file(self._file_path)
                    self.report({"INFO"}, f"Saved Shot{self.shot_id} at {self._file_path}")   
                    return {'FINISHED'}
                except FileExistsError:
                    self.report({"ERROR"}, f"Cannot create a file/folder when that file/folder already exists {file_path}") 
                    return {'CANCELLED'}
            self.report({"INFO"}, f"Built Shot {self.shot_id}, file is not saved!") 
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        project = cache.project_active_get()

        if addon_prefs.session.is_auth() is False:
            self.report(
                {'ERROR'}, "Must be logged into Kitsu to continue. Check login status in 'Blender Kitsu' addon preferences.") 
            return {'CANCELLED'}
        
        if project.id == "":
            self.report(
                {'ERROR'}, "Operator is not able to determine the Kitsu production's name. Check project is selected in 'Blender Kitsu' addon preferences.") 
            return {'CANCELLED'}
        
        if not addon_prefs.is_project_root_valid:
            self.report(
                {'ERROR'}, "Operator is not able to determine the project root directory. Check project root directiory is configured in 'Blender Kitsu' addon preferences.")
            return {'CANCELLED'}
        
        if not addon_prefs.is_editorial_dir_valid:
            self.report(
                {'ERROR'}, "Shot builder is dependant on a valid editorial export path and file pattern. Check Preferences, errors appear in console")
            return {'CANCELLED'}
        
        self.production_root = addon_prefs.project_root_dir
        self.production_name = project.name


        ensure_loaded_production(context)
        production = get_active_production()

        
        self.production_root = addon_prefs.project_root_dir
        self.production_name = project.name

        global _production_task_type_items
        _production_task_type_items = production.get_task_type_items(
            context=context)

        global _production_seq_id_items
        _production_seq_id_items = production.get_seq_items(context=context)

        global _production_shots
        _production_shots = production.get_shots(context=context)

        return cast(Set[str], context.window_manager.invoke_props_dialog(self, width=400))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        if not self.production_root:
            self.report(
                {'ERROR'}, "Shot builder can only be started from the File menu. Shortcuts like CTRL-N don't work")
            return {'CANCELLED'}
        if self._built_shot:
            return {'RUNNING_MODAL'}
        addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences
        ensure_loaded_production(context)
        production = get_active_production()
        shot_builder = ShotBuilder(
            context=context, production=production, shot_name=self.shot_id, task_type=TaskType(self.task_type))
        shot_builder.create_build_steps()
        shot_builder.build()
        
        # Build Kitsu Context
        sequence = gazu.shot.get_sequence_by_name(production.config['KITSU_PROJECT_ID'], self.seq_id)
        shot = gazu.shot.get_shot_by_name(sequence, self.shot_id)

        #Load EDIT
        editorial_export_get_latest(context, shot)      
        # Load Anim Workspace
        animation_workspace_delete_others()

        # Initilize armatures
        for obj in [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]:
            base_name = obj.name.split(addon_prefs.shot_builder_armature_prefix)[-1] 
            new_action = bpy.data.actions.new(f"{addon_prefs.shot_builder_action_prefix}{base_name}.{self.shot_id}.v001")
            new_action.use_fake_user = True
            obj.animation_data.action = new_action
        
        # Set Shot Frame Range  
        frame_length = shot.get('nb_frames')
        context.scene.frame_start = addon_prefs.shot_builder_frame_offset
        context.scene.frame_end = frame_length + addon_prefs.shot_builder_frame_offset

        # Run User Script
        exec(addon_prefs.user_exec_code)

        self._file_path = shot_builder.build_context.shot.file_path   
        self._built_shot = True
        return {'RUNNING_MODAL'}


    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.prop(self, "production_name")
        layout.prop(self, "seq_id")
        layout.prop(self, "shot_id")
        layout.prop(self, "task_type")
        layout.prop(self, "auto_save")
