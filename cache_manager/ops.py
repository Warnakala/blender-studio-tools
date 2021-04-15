import bpy
import re
from typing import List, Any, Set, cast
from pathlib import Path

from .logger import LoggerFactory
from . import blend, prefs, props, opsdata, cmglobals

logger = LoggerFactory.getLogger(__name__)


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class CM_OT_cache_export(bpy.types.Operator):
    """"""

    bl_idname = "cm.cache_export"
    bl_label = "Export Cache"
    bl_description = "Exports alembic cache for selected collections"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return [context.scene.collection] and addon_prefs.is_cachedir_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        succeeded = []
        failed = []
        logger.info("-START- Exporting Cache")

        # already of type Path, convenience auto complete
        cachedir_path = Path(addon_prefs.cachedir_path)
        collections = list(props.get_cache_collections(context))

        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        for idx, coll in enumerate(collections):
            context.window_manager.progress_update(idx)
            # identifier if coll is valid?

            # deselect all
            bpy.ops.object.select_all(action="DESELECT")

            # create selection for alembic_export operator
            for obj in coll.all_objects:
                if obj.type in cmglobals.VALID_OBJECT_TYPES and obj.name.startswith(
                    "GEO"
                ):
                    logger.info("Valid object: %s", obj.name)
                    obj.select_set(True)

            filepath = cachedir_path / blend.gen_filename_collection(coll)

            if filepath.exists():
                logger.warning(
                    "Filepath %s already exists. Will overwrite.", filepath.as_posix()
                )

            try:
                # for each collection create seperate alembic
                bpy.ops.wm.alembic_export(
                    filepath=filepath.as_posix(),
                    start=context.scene.frame_start,
                    end=context.scene.frame_end,
                    xsamples=1,
                    gsamples=1,
                    sh_open=0,
                    sh_close=1,
                    selected=True,
                    renderable_only=False,
                    visible_objects_only=False,
                    flatten=True,
                    uvs=True,
                    packuv=True,
                    normals=True,
                    vcolors=False,
                    face_sets=True,
                    subdiv_schema=False,
                    apply_subdiv=False,
                    curves_as_mesh=True,
                    use_instancing=True,
                    global_scale=1,
                    triangulate=False,
                    quad_method="SHORTEST_DIAGONAL",
                    ngon_method="BEAUTY",
                    export_hair=False,
                    export_particles=False,
                    export_custom_properties=True,
                    as_background_job=False,
                    init_scene_frame_range=False,
                )
            except Exception as e:
                logger.info("Failed to export %s", coll.name)
                logger.exception(str(e))
                failed.append(coll)
                continue

            succeeded.append(coll)
            logger.info("Exported %s to %s", coll.name, filepath.as_posix())

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Exported {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        logger.info("-END- Exporting Cache")
        return {"FINISHED"}


class CM_OT_cache_list_actions(bpy.types.Operator):
    """Move items up and down, add and remove"""

    bl_idname = "cm.cache_list_actions"
    bl_label = "Cache List Actions"
    bl_description = "Add and remove items"
    bl_options = {"REGISTER"}

    action: bpy.props.EnumProperty(items=(("ADD", "Add", ""), ("REMOVE", "Remove", "")))

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        scn = context.scene
        idx = scn.cm_collections_index

        try:
            item = scn.cm_collections[idx]
        except IndexError:
            pass
        else:
            if self.action == "REMOVE":
                item = scn.cm_collections[scn.cm_collections_index]
                item_name = item.name
                scn.cm_collections.remove(idx)
                scn.cm_collections_index -= 1
                info = "Item %s removed from cache list" % (item_name)
                self.report({"INFO"}, info)

        if self.action == "ADD":
            act_coll = context.view_layer.active_layer_collection.collection
            if act_coll.name in [c[1].name for c in scn.cm_collections.items()]:
                info = '"%s" already in the list' % (act_coll.name)
            else:
                item = scn.cm_collections.add()
                item.coll_ptr = act_coll
                item.name = item.coll_ptr.name
                scn.cm_collections_index = len(scn.cm_collections) - 1
            info = "%s added to list" % (item.name)
            self.report({"INFO"}, info)

        return {"FINISHED"}


class CM_OT_assign_cachefile(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "cm.assign_cachefile"
    bl_label = "Assign Cachefile"
    bl_options = {"INTERNAL"}
    bl_property = "cachefile"

    cachefile: bpy.props.EnumProperty(
        items=opsdata.get_cachefiles_enum, name="Cachefiles"
    )
    index: bpy.props.IntProperty(name="Index")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # collections = scn.cm_collections[scn.cm_collections_index]
        if not self.cachefile:
            self.report({"WARNING"}, f"Please select a valid cachefile")
            return {"CANCELLED"}

        collection = context.scene.cm_collections[self.index].coll_ptr
        collection.cm.cachefile = self.cachefile

        self.report({"INFO"}, f"{collection.name} assigned cachefile {self.cachefile}")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class CM_OT_cache_import(bpy.types.Operator):
    bl_idname = "cm.cache_import"
    bl_label = "Import Cache"
    bl_description = "Imports alembic cache for collections"

    def execute(self, context):
        addon_prefs = prefs.addon_prefs_get(context)
        succeeded = []
        failed = []
        modifier_name = cmglobals.MODIFIER_NAME
        constraint_name = cmglobals.CONSTRAINT_NAME
        collections = list(props.get_cache_collections(context))

        logger.info("-START- Importing Cache")

        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        for idx, coll in enumerate(collections):
            context.window_manager.progress_update(idx)

            # skip if  no cachefile assigned
            if not coll.cm.cachefile:
                failed.append(coll)
                logger.warning("%s has no cachefile assigned. Skip.", coll.name)
                continue

            # get cachefile path for this collection
            cachefile_path = coll.cm.cachefile
            cachefile_name = Path(cachefile_path).name

            # import Alembic Cache. if its already imported reload it
            try:
                bpy.data.cache_files[cachefile_name]
            except KeyError:
                bpy.ops.cachefile.open(filepath=cachefile_path)
            else:
                bpy.ops.cachefile.reload()

            abc_cache = bpy.data.cache_files[cachefile_name]
            abc_cache.scale = 1

            # Create a List with all selected Objects
            object_list = [
                obj
                for obj in coll.all_objects
                if obj.type in cmglobals.VALID_OBJECT_TYPES
                and obj.name.startswith("GEO")
            ]

            # Loop Through All Objects except Active Object and add Modifier and Constraint
            for obj in object_list:
                # remove all armature modifiers
                index = self._rm_armature_modifier(obj)
                modifier_index = index if index != -1 else 0

                # modifier_index = 0

                # if modifier does not exist yet create it
                # move modifier and constraint to index 0 in stack
                # as we need to use bpy.ops for that object needs to be active
                bpy.context.view_layer.objects.active = obj
                if obj.modifiers.find(modifier_name) != 0:
                    mod = obj.modifiers.new(modifier_name, "MESH_SEQUENCE_CACHE")
                    bpy.ops.object.modifier_move_to_index(
                        modifier=modifier_name, index=modifier_index
                    )  # TODO: does not work with library overwritten files

                # if constraint does not exist yet create it
                if obj.constraints.find(constraint_name) != 0:
                    con = obj.constraints.new("TRANSFORM_CACHE")
                    con.name = constraint_name
                    bpy.ops.constraint.move_to_index(
                        constraint=constraint_name, index=0
                    )  # TODO: does not work with library overwritten files

                # Set Settings of Modifier and Constraints
                mod = obj.modifiers.get(modifier_name)
                mod.cache_file = abc_cache

                # if object is duplicated (multiple copys of the same object that get different cachses)
                # we have to kill the .001 postfix that gets created auto on duplication
                # otherwise object path is not valid
                object_name = self._kill_increment(obj.name)
                object_data_name = self._kill_increment(obj.data.name)

                mod.object_path = "/" + object_name + "/" + object_data_name

                con = obj.constraints.get(constraint_name)
                con.cache_file = abc_cache
                con.object_path = "/" + object_name + "/" + object_data_name

            logger.info("%s imported cache %s", coll.name, cachefile_path)

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Importing Cache for {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        logger.info("-END- Importing Cache")
        return {"FINISHED"}

    def _kill_increment(self, str_value: str) -> str:
        return str_value
        match = re.search("\.\d\d\d", str_value)
        if match:
            return str_value.replace(match.group(0), "")
        return str_value

    def _rm_armature_modifier(self, obj: bpy.types.Object) -> int:
        modifiers = list(obj.modifiers)
        a_index: int = -1
        for idx, m in enumerate(modifiers):
            if m.type == "ARMATURE":
                logger.info("Removing modifier: %s", m.name)
                obj.modifiers.remove(m)
                if a_index == -1:
                    a_index = idx
        return a_index


# ---------REGISTER ----------

classes: List[Any] = [
    CM_OT_cache_export,
    CM_OT_cache_import,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
