import bpy
import re
import contextlib
from typing import List, Any, Set, cast
from pathlib import Path

from .logger import LoggerFactory, gen_processing_string, log_new_lines
from . import cache, prefs, props, opsdata, cmglobals
from .cache import CacheConfigFactory

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

    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )
    index: bpy.props.IntProperty(name="Index")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return [context.scene.collection] and addon_prefs.is_cachedir_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        cacheconfig_path = addon_prefs.cacheconfig_path
        succeeded = []
        failed = []
        log_new_lines(1)
        logger.info("-START- Exporting Cache")

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_export(context))
        else:
            collections = [context.scene.cm_collections_export[self.index].coll_ptr]

        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        for idx, coll in enumerate(collections):
            log_new_lines(2)
            logger.info("%s", gen_processing_string(coll.name))

            context.window_manager.progress_update(idx)
            # identifier if coll is valid?

            # deselect all
            bpy.ops.object.select_all(action="DESELECT")

            # create object list to be exported
            object_list = cache.get_valid_cache_objects(coll)

            # mute drivers
            muted_drivers = opsdata.disable_drivers(object_list)

            logger.info(
                "Disabled drivers for export:\n%s",
                ",\n".join([f"{d.id_data.name}: {d.data_path}" for d in muted_drivers]),
            )
            # ensure that all objects are visible for export
            objs_to_be_hidden = opsdata.ensure_obj_vis(object_list)

            logger.info(
                "Show objects in viewport for export:\n%s",
                ",\n".join([obj.name for obj in objs_to_be_hidden]),
            )

            # ensure the all collections are visible for export
            # otherwise object in it will not be exported
            colls_to_be_hidden = opsdata.ensure_coll_vis(coll)

            logger.info(
                "Show collections in viewport for export:\n%s",
                ",\n".join([coll.name for coll in colls_to_be_hidden]),
            )

            # select objects for bpy.ops.wm.alembic_export
            for obj in object_list:
                obj.select_set(True)

            # filepath
            filepath = cache.gen_cachepath_collection(coll, context)
            if filepath.exists():
                logger.warning(
                    "Filepath %s already exists. Will overwrite.", filepath.as_posix()
                )

            # export
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

            # hide objs again
            for obj in objs_to_be_hidden:
                obj.hide_viewport = True

            logger.info(
                "Hide objects in viewport after export:\n%s",
                ",\n".join([obj.name for obj in objs_to_be_hidden]),
            )

            # hide colls again
            for coll in colls_to_be_hidden:
                obj.hide_viewport = True

            logger.info(
                "Hide collections in viewport after export:\n%s",
                ",\n".join([coll.name for coll in colls_to_be_hidden]),
            )

            # entmute driver
            opsdata.enable_drivers(muted_drivers)

            logger.info(
                "Enabled drivers after export:\n%s",
                ",\n".join([f"{d.id_data.name}: {d.data_path}" for d in muted_drivers]),
            )

            # success log for this collections
            logger.info("Exported %s to %s", coll.name, filepath.as_posix())
            succeeded.append(coll)

        # generate cacheconfig
        CacheConfigFactory.gen_config_from_colls(context, collections, cacheconfig_path)

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Exported {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        log_new_lines(1)
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

        scn_category = scn.cm_collections_export
        idx = scn.cm_collections_export_index

        if context.scene.cm_category == "IMPORT":
            scn_category = scn.cm_collections_import
            idx = scn.cm_collections_import_index

        try:
            item = scn_category[idx]
        except IndexError:
            pass
        else:
            if self.action == "REMOVE":
                item = scn_category[idx]
                item_name = item.name
                scn_category.remove(idx)
                idx -= 1
                info = "Item %s removed from cache list" % (item_name)
                self.report({"INFO"}, info)

        if self.action == "ADD":
            act_coll = context.view_layer.active_layer_collection.collection
            if act_coll.name in [c[1].name for c in scn_category.items()]:
                info = '"%s" already in the list' % (act_coll.name)
            else:
                item = scn_category.add()
                item.coll_ptr = act_coll
                item.name = item.coll_ptr.name
                idx = len(scn_category) - 1
            info = "%s added to list" % (item.name)
            self.report({"INFO"}, info)

        return {"FINISHED"}


class CM_OT_import_collections(bpy.types.Operator):
    """Move items up and down, add and remove"""

    bl_idname = "cm.import_collections"
    bl_label = "Import Colletions"
    bl_description = "Import Colletions from Cacheconfig"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return addon_prefs.is_cacheconfig_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        cacheconfig_path = addon_prefs.cacheconfig_path

        log_new_lines(1)
        logger.info("-START- Importing Collections")

        cacheconfig = CacheConfigFactory.load_config_from_file(cacheconfig_path)
        cacheconfig.import_collections(context)

        log_new_lines(1)
        logger.info("-END- Importing Collections")

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

        collection = context.scene.cm_collections_import[self.index].coll_ptr
        collection.cm.cachefile = self.cachefile

        self.report({"INFO"}, f"{collection.name} assigned cachefile {self.cachefile}")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class CM_OT_import_cache(bpy.types.Operator):
    bl_idname = "cm.import_cache"
    bl_label = "Import Cache"
    bl_description = (
        "Imports alembic cache and animationdata from cacheconfig for collections"
    )

    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )
    index: bpy.props.IntProperty(name="Index")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return addon_prefs.is_cacheconfig_valid

    def execute(self, context):
        log_new_lines(1)
        logger.info("-START- Importing Cache")
        addon_prefs = prefs.addon_prefs_get(context)
        cacheconfig_path = addon_prefs.cacheconfig_path
        cacheconfig = CacheConfigFactory.load_config_from_file(cacheconfig_path)

        succeeded = []
        failed = []
        modifier_name = cmglobals.MODIFIER_NAME
        constraint_name = cmglobals.CONSTRAINT_NAME

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_import(context))
        else:
            collections = [context.scene.cm_collections_import[self.index].coll_ptr]

        # skip if  no cachefile assigned
        valid_colls = []
        for coll in collections:
            if not coll.cm.cachefile:
                failed.append(coll)
                logger.warning("%s has no cachefile assigned. Skip.", coll.name)
                continue
            valid_colls.append(coll)

        collections = valid_colls

        # load animation data from config
        cacheconfig.import_animation_data(collections)

        log_new_lines(1)
        logger.info("-START- Importing Alembic Cache")
        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        # load alembic as mesh sequence cache
        for idx, coll in enumerate(collections):
            context.window_manager.progress_update(idx)
            log_new_lines(2)
            logger.info("%s", gen_processing_string(coll.name))

            # ensure cachefile is loaded or reloaded
            cachefile = self._ensure_cachefile(coll.cm.cachefile)

            # get list with valid objects to apply cache to
            object_list = cache.get_valid_cache_objects(coll)

            # Loop Through All Objects except Active Object and add Modifier and Constraint
            for obj in object_list:
                # remove all armature modifiers, get index of first one, use that index for cache modifier
                a_index = self._disable_modifiers(obj)
                modifier_index = a_index if a_index != -1 else 0

                # ensure cache modifier and constraint
                mod = self._ensure_cache_modifier(obj)
                con = self._ensure_cache_constraint(obj)

                # config cache modifier and constraint
                self._config_cache_modifier(context, mod, modifier_index, cachefile)
                self._config_cache_constraint(context, con, cachefile)

            # set is_cache_loaded property
            coll.cm.is_cache_loaded = True

            logger.info("%s imported cache %s", coll.name, cachefile.filepath)
            succeeded.append(coll)

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Importing Cache for {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        log_new_lines(1)
        logger.info("-END- Importing Alembic Cache")
        log_new_lines(1)
        logger.info("-END- Importing Cache")
        return {"FINISHED"}

    def _kill_increment(self, str_value: str) -> str:
        return str_value
        match = re.search("\.\d\d\d", str_value)
        if match:
            return str_value.replace(match.group(0), "")
        return str_value

    def _rm_modifiers(self, obj: bpy.types.Object) -> int:
        modifiers = list(obj.modifiers)
        a_index: int = -1
        rm_mods = []
        for idx, m in enumerate(modifiers):
            if m.type not in opsdata.MODIFIERS_KEEP:

                obj.modifiers.remove(m)
                rm_mods.append(m.name)

                # save index of first armature modifier to
                if a_index == -1 and m.type == "ARMATURE":
                    a_index = idx

        logger.info("%s Removed modifiers: %s", obj.name, ", ".join(rm_mods))
        return a_index

    def _disable_modifiers(self, obj: bpy.types.Object) -> int:
        modifiers = list(obj.modifiers)
        a_index: int = -1
        disabled_mods = []
        for idx, m in enumerate(modifiers):
            if m.type not in opsdata.MODIFIERS_KEEP:
                m.show_viewport = False
                m.show_render = False
                m.show_in_editmode = False
                disabled_mods.append(m.name)

                # save index of first armature modifier to
                if a_index == -1 and m.type == "ARMATURE":
                    a_index = idx

        logger.info("%s Disabled modifiers: %s", obj.name, ", ".join(disabled_mods))
        return a_index

    def _ensure_cachefile(self, cachefile_path: str) -> bpy.types.CacheFile:
        # get cachefile path for this collection
        cachefile_name = Path(cachefile_path).name

        # import Alembic Cache. if its already imported reload it
        try:
            bpy.data.cache_files[cachefile_name]
        except KeyError:
            bpy.ops.cachefile.open(filepath=cachefile_path)
        else:
            bpy.ops.cachefile.reload()

        cachefile = bpy.data.cache_files[cachefile_name]
        cachefile.scale = 1
        return cachefile

    def _ensure_cache_modifier(
        self, obj: bpy.types.Object
    ) -> bpy.types.MeshSequenceCacheModifier:
        modifier_name = cmglobals.MODIFIER_NAME
        # if modifier does not exist yet create it
        if obj.modifiers.find(modifier_name) == -1:  # not found
            mod = obj.modifiers.new(modifier_name, "MESH_SEQUENCE_CACHE")
        else:
            logger.info(
                "Object: %s already has %s modifier. Will use that.",
                obj.name,
                modifier_name,
            )
        mod = obj.modifiers.get(modifier_name)
        return mod

    def _ensure_cache_constraint(
        self, obj: bpy.types.Object
    ) -> bpy.types.TransformCacheConstraint:
        constraint_name = cmglobals.CONSTRAINT_NAME
        # if constraint does not exist yet create it
        if obj.constraints.find(constraint_name) == -1:  # not found
            con = obj.constraints.new("TRANSFORM_CACHE")
            con.name = constraint_name
        else:
            logger.info(
                "Object: %s already has %s constraint. Will use that.",
                obj.name,
                constraint_name,
            )
        con = obj.constraints.get(constraint_name)
        return con

    def _config_cache_modifier(
        self,
        context: bpy.types.Context,
        mod: bpy.types.MeshSequenceCacheModifier,
        modifier_index: int,
        cachefile: bpy.types.CacheFile,
    ) -> bpy.types.MeshSequenceCacheModifier:
        obj = mod.id_data
        # move to index
        # as we need to use bpy.ops for that object needs to be active
        bpy.context.view_layer.objects.active = obj
        override = context.copy()
        override["modifier"] = mod
        bpy.ops.object.modifier_move_to_index(
            override, modifier=mod.name, index=modifier_index
        )
        # adjust settings
        mod.cache_file = cachefile
        mod.object_path = self._gen_object_path(obj)

        return mod

    def _config_cache_constraint(
        self,
        context: bpy.types.Context,
        con: bpy.types.TransformCacheConstraint,
        cachefile: bpy.types.CacheFile,
    ) -> bpy.types.TransformCacheConstraint:
        obj = con.id_data
        # move to index
        # as we need to use bpy.ops for that object needs to be active
        bpy.context.view_layer.objects.active = obj
        override = context.copy()
        override["constraint"] = con
        bpy.ops.constraint.move_to_index(override, constraint=con.name, index=0)

        # adjust settings
        con.cache_file = cachefile
        con.object_path = self._gen_object_path(obj)

        return con

    def _gen_object_path(self, obj: bpy.types.Object) -> str:
        # if object is duplicated (multiple copys of the same object that get different cachses)
        # we have to kill the .001 postfix that gets created auto on duplication
        # otherwise object path is not valid

        object_name = self._kill_increment(obj.name)
        object_data_name = self._kill_increment(obj.data.name)
        object_path = "/" + object_name + "/" + object_data_name

        # dot and whitespace not valid in abc tree will be replaced with underscore
        replace = [" ", "."]
        for char in replace:
            object_path = object_path.replace(char, "_")

        return object_path


class CM_OT_cache_hide(bpy.types.Operator):
    bl_idname = "cm.cache_hide"
    bl_label = "Hide Cache"
    bl_description = "Hide mesh sequence cache modifier and transform cache constraint"

    index: bpy.props.IntProperty(name="Index")
    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )

    def execute(self, context):
        modifier_name = cmglobals.MODIFIER_NAME
        constraint_name = cmglobals.CONSTRAINT_NAME

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_import(context))
        else:
            collections = [context.scene.cm_collections_import[self.index].coll_ptr]

        logger.info("-START- Hiding Cache")

        for idx, coll in enumerate(collections):
            # Create a List with all selected Objects
            object_list = cache.get_valid_cache_objects(coll)

            # Loop Through All Objects
            for obj in object_list:
                # Set Settings of Modifier
                if not obj.modifiers.find(modifier_name) == -1:
                    mod = obj.modifiers.get(modifier_name)
                    mod.show_viewport = False
                    mod.show_render = False

                if not obj.constraints.find(constraint_name) == -1:
                    con = obj.constraints.get(constraint_name)
                    con.mute = True

            # set is_cache_hidden prop for ui
            coll.cm.is_cache_hidden = True

            logger.info("Hide Cache for %s", coll.name)

        self.report(
            {"INFO"},
            f"Hid Cache of {len(collections)} Collections",
        )

        logger.info("-END- Hiding Cache")

        return {"FINISHED"}


class CM_OT_cache_show(bpy.types.Operator):
    bl_idname = "cm.cache_show"
    bl_label = "Show Cache"
    bl_description = "Show mesh sequence cache modifier and transform cache constraint"

    index: bpy.props.IntProperty(name="Index")
    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )

    def execute(self, context):
        modifier_name = cmglobals.MODIFIER_NAME
        constraint_name = cmglobals.CONSTRAINT_NAME

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_import(context))
        else:
            collections = [context.scene.cm_collections_import[self.index].coll_ptr]

        logger.info("-START- Unhiding Cache")

        for idx, coll in enumerate(collections):
            # Create a List with all selected Objects
            object_list = cache.get_valid_cache_objects(coll)

            # Loop Through All Objects
            for obj in object_list:
                # Set Settings of Modifier and Constraint
                if not obj.modifiers.find(modifier_name) == -1:
                    mod = obj.modifiers.get(modifier_name)
                    mod.show_viewport = True
                    mod.show_render = True

                if not obj.constraints.find(constraint_name) == -1:
                    con = obj.constraints.get(constraint_name)
                    con.mute = False

            # set is_cache_hidden prop for ui
            coll.cm.is_cache_hidden = False

            logger.info("Unhid Cache for %s", coll.name)

        self.report(
            {"INFO"},
            f"Unhid Cache of {len(collections)} Collections",
        )

        logger.info("-END- Hiding Cache")
        return {"FINISHED"}


class CM_OT_cache_remove(bpy.types.Operator):
    bl_idname = "cm.cache_remove"
    bl_label = "Remove Cache"

    index: bpy.props.IntProperty(name="Index")
    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )

    def execute(self, context):
        context = bpy.context
        modifier_name = cmglobals.MODIFIER_NAME
        constraint_name = cmglobals.CONSTRAINT_NAME

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_import(context))
        else:
            collections = [context.scene.cm_collections_import[self.index].coll_ptr]

        logger.info("-START- Removing Cache")

        for idx, coll in enumerate(collections):
            # Create a List with all selected Objects
            object_list = cache.get_valid_cache_objects(coll)

            # Loop Through All Objects and remove Modifier and Constraint
            for obj in object_list:
                if not obj.modifiers.find(modifier_name) == -1:
                    mod = obj.modifiers.get(modifier_name)
                    obj.modifiers.remove(mod)

                if not obj.constraints.find(constraint_name) == -1:
                    con = obj.constraints.get(constraint_name)
                    obj.constraints.remove(con)

            # set is_cache_loaded property
            coll.cm.is_cache_loaded = False

            logger.info("Remove Cache for %s", coll.name)

        self.report(
            {"INFO"},
            f"Removed Cache of {len(collections)} Collections",
        )

        logger.info("-END- Removing Cache")
        return {"FINISHED"}


# ---------REGISTER ----------

classes: List[Any] = [
    CM_OT_cache_export,
    CM_OT_import_cache,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
    CM_OT_cache_show,
    CM_OT_cache_hide,
    CM_OT_cache_remove,
    CM_OT_import_collections,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
