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

from typing import List, Any, Set, cast, Tuple, Dict
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

from cache_manager import cache, props, propsdata, opsdata, cmglobals
from cache_manager.logger import LoggerFactory, gen_processing_string, log_new_lines
from cache_manager.cache import CacheConfigFactory, CacheConfigProcessor

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
    confirm: bpy.props.BoolProperty(
        name="Confirm", description="Confirm to overwrite", default=True
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # remove invalid collections
        collections = [
            coll
            for coll in props.get_cache_collections_export(context)
            if cache.is_valid_cache_coll(coll)
        ]
        return bool(context.scene.cm.is_cachedir_valid and collections)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Exporting cache aborted.")
            return {"CANCELLED"}

        cacheconfig_path: Path = context.scene.cm.cacheconfig_path
        succeeded: List[bpy.types.Collection] = []
        failed: List[bpy.types.Collection] = []

        log_new_lines(1)

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_export(context))
        else:
            collections = [context.scene.cm.colls_export[self.index].coll_ptr]

        # remove invalid collections
        collections = [coll for coll in collections if cache.is_valid_cache_coll(coll)]

        logger.info(
            "-START- Exporting Cache of: %s", ", ".join([c.name for c in collections])
        )

        # create ouput dir if not existent
        filedir = Path(context.scene.cm.cachedir_path)
        if not filedir.exists():
            filedir.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory %s", filedir.as_posix())

        # frame range
        frame_range = opsdata.get_cache_frame_range(context)

        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        # create new scene
        scene_orig = bpy.context.scene
        bpy.ops.scene.new(type="EMPTY")  # changes active scene
        scene_tmp = bpy.context.scene
        scene_tmp.name = "cm_tmp_export"
        logger.info("Create tmp scene for export: %s", scene_tmp.name)

        # disable simplify
        was_simplify = bpy.context.scene.render.use_simplify
        opsdata.set_simplify(False)

        for idx, coll in enumerate(collections):

            # HAPPENS IN TMP SCENE

            # log
            log_new_lines(2)
            logger.info("%s", gen_processing_string(coll.name))
            context.window_manager.progress_update(idx)

            # unlink all children of scene collection
            colls_unlink = list(context.scene.collection.children)
            colls_unlink.reverse()

            for ucoll in colls_unlink:
                context.scene.collection.children.unlink(ucoll)
                logger.info("%s unlink collection: %s", context.scene.name, ucoll.name)

            # link in collection
            context.scene.collection.children.link(coll)
            logger.info("%s linked collection: %s", context.scene.name, coll.name)

            # hide_render other cache collections for faster export
            cache_colls_active_exluded = collections.copy()
            cache_colls_active_exluded.remove(coll)
            excluded_colls_to_restore_vis = opsdata.set_item_vis(
                cache_colls_active_exluded, False
            )

            # deselect all
            bpy.ops.object.select_all(action="DESELECT")

            # create object list to be exported
            object_list = cache.get_valid_cache_objects(coll)

            # mute drivers
            muted_vis_drivers = opsdata.disable_vis_drivers(object_list, modifiers=True)

            # ensure modifiers vis have render vis settings does not include MODIFIERS_KEEP
            mods_restore_vis_from_sync = opsdata.sync_modifier_vis_with_render_setting(
                object_list
            )

            # ensure MODIFIERS_KEEP are disabled for export (they will be enabled on import)
            mods_restore_vis_from_keep = opsdata.config_modifiers_keep_state(
                object_list, enable=False
            )

            # apply modifier suffix visibily override (.nocache) > will set show_viewport, show_render to False
            mods_restore_vis_from_suffix = opsdata.apply_modifier_suffix_vis_override(
                object_list, "EXPORT"
            )

            # gen one list of tuples that contains each modifier with its original vis settings once
            mods_to_restore_vis = self._construct_mod_to_restore_vis_list(
                mods_restore_vis_from_sync,
                mods_restore_vis_from_keep,
                mods_restore_vis_from_suffix,
            )

            # ensure the all collections are visible for export
            # otherwise object in it will not be exported
            colls_to_restore_vis = opsdata.set_item_vis(
                list(opsdata.traverse_collection_tree(coll)), True
            )

            # ensure that all objects are visible for export
            objs_to_restore_vis = opsdata.set_item_vis(object_list, True)

            # set instancing type of emptys to none
            empties_to_restore = opsdata.set_instancing_type_of_empties(
                object_list, "NONE"
            )

            # select objects for bpy.ops.wm.alembic_export
            for obj in object_list:
                obj.select_set(True)

            # filepath
            filepath = Path(propsdata.gen_cachepath_collection(coll, context))
            if filepath.exists():
                logger.warning(
                    "Filepath %s already exists. Will overwrite.", filepath.as_posix()
                )

            # export
            try:
                logger.info("Start alembic export of %s", coll.name)
                # for each collection create seperate alembic
                bpy.ops.wm.alembic_export(
                    filepath=filepath.as_posix(),
                    start=frame_range[0],
                    end=frame_range[1],
                    xsamples=context.scene.cm.xsamples,
                    gsamples=context.scene.cm.gsamples,
                    sh_open=context.scene.cm.sh_open,
                    sh_close=context.scene.cm.sh_close,
                    selected=True,
                    visible_objects_only=False,
                    flatten=True,
                    uvs=True,
                    packuv=True,
                    normals=True,
                    vcolors=False,
                    face_sets=True,
                    subdiv_schema=False,
                    apply_subdiv=True,
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
                logger.info("Alembic export of %s finished", coll.name)

            except Exception as e:
                logger.info("Failed to export %s", coll.name)
                logger.exception(str(e))
                failed.append(coll)
                continue

            # restore instancing types of empties
            opsdata.restore_instancing_type(empties_to_restore)

            # hide objs again
            opsdata.restore_item_vis(objs_to_restore_vis)

            # hide colls again
            opsdata.restore_item_vis(colls_to_restore_vis)

            # restore modifier viewport vis / render vis
            opsdata.restore_modifier_vis(mods_to_restore_vis)

            # entmute driver
            opsdata.enable_muted_drivers(muted_vis_drivers)

            # include other cache collections again
            opsdata.restore_item_vis(excluded_colls_to_restore_vis)

            # success log for this collections
            logger.info("Exported %s to %s", coll.name, filepath.as_posix())
            succeeded.append(coll)

        # restore simplify state
        opsdata.set_simplify(was_simplify)

        # change to original scene
        bpy.context.window.scene = scene_orig
        logger.info("Set active scene: %s", context.scene.name)

        # delete tmp scene
        logger.info("Remove tmp scene: %s", scene_tmp.name)
        bpy.data.scenes.remove(scene_tmp)

        # generate cacheconfig
        CacheConfigFactory.gen_config_from_colls(context, collections, cacheconfig_path)

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        # update cache version property to jump to latest version
        propsdata.update_cache_version_property(context)

        # if it was do all reset after
        if self.do_all:
            self.do_all = False

        # log
        self.report(
            {"INFO"},
            f"Exported {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        log_new_lines(1)
        logger.info(
            "-END- Exporting Cache of %s", ", ".join([c.name for c in succeeded])
        )

        # clear deleted collections from list
        propsdata.rm_deleted_colls_from_list(context)

        return {"FINISHED"}

    def invoke(self, context, event):
        filedir = Path(context.scene.cm.cachedir_path)
        if filedir.exists():
            self.confirm = False
            return context.window_manager.invoke_props_dialog(self, width=300)

        return self.execute(context)

    def draw(self, context):
        # UI
        layout = self.layout

        # label
        filedir = Path(context.scene.cm.cachedir_path)
        row = layout.row()
        row.label(text=f"{filedir.as_posix()} already exists.", icon="ERROR")

        # confirm dialog
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Overwrite?",
        )

    def _construct_mod_to_restore_vis_list(
        self, *args: List[Tuple[bpy.types.Modifier, bool, bool]]
    ) -> List[Tuple[bpy.types.Modifier, bool, bool]]:

        mods_to_restore_vis: List[Tuple[bpy.types.Modifier, bool, bool]] = []

        for arg in args:
            for mod, show_viewport, show_render in arg:
                if mod not in [m for m, v, r in mods_to_restore_vis]:
                    mods_to_restore_vis.append((mod, show_viewport, show_render))

        return mods_to_restore_vis


class CM_OT_cacheconfig_export(bpy.types.Operator):
    """"""

    bl_idname = "cm.cacheconfig_export"
    bl_label = "Export Cacheconfig"
    bl_description = "Exports only the cacheconfig for selected collections"

    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=False
    )
    index: bpy.props.IntProperty(name="Index")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # remove invalid collections
        collections = [
            coll
            for coll in props.get_cache_collections_export(context)
            if cache.is_valid_cache_coll(coll)
        ]
        return bool(context.scene.cm.is_cachedir_valid and collections)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cacheconfig_path = context.scene.cm.cacheconfig_path
        log_new_lines(1)
        logger.info("-START- Exporting Cacheconfig")

        # clear deleted collections from list
        propsdata.rm_deleted_colls_from_list(context)

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_export(context))
        else:
            collections = [context.scene.cm.colls_export[self.index].coll_ptr]

        # remove invalid collections
        collections = [coll for coll in collections if cache.is_valid_cache_coll(coll)]

        # create ouput dir if not existent
        filedir = Path(context.scene.cm.cachedir_path)
        if not filedir.exists():
            filedir.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory %s", filedir.as_posix())

        # generate cacheconfig
        CacheConfigFactory.gen_config_from_colls(context, collections, cacheconfig_path)

        # update cache version property to jump to latest version
        propsdata.update_cache_version_property(context)

        # log
        self.report(
            {"INFO"},
            f"Exported Cacheconfig {cacheconfig_path.as_posix()}",
        )

        log_new_lines(1)
        logger.info("-END- Exporting Cacheconfig")
        return {"FINISHED"}


class CM_OT_cache_list_actions(bpy.types.Operator):
    """Move items up and down, add and remove"""

    bl_idname = "cm.cache_list_actions"
    bl_label = "Cache List Actions"
    bl_description = "Add and remove items"
    bl_options = {"REGISTER"}

    action: bpy.props.EnumProperty(items=(("ADD", "Add", ""), ("REMOVE", "Remove", "")))

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if self.action == "REMOVE":
            result = opsdata.rm_coll_from_cache_collections(
                context, context.scene.cm.category
            )
            if not result:
                return {"CANCELLED"}

            info = (
                f"Removed {result.name} from {context.scene.cm.category.lower()} list"
            )
            self.report({"INFO"}, info)

        if self.action == "ADD":
            act_coll = context.view_layer.active_layer_collection.collection

            if opsdata.is_item_local(act_coll):
                self.report(
                    {"ERROR"}, f"Blend files needs to be saved to add local collection"
                )
                return {"FINISHED"}

            result = opsdata.add_coll_to_cache_collections(
                context, act_coll, context.scene.cm.category
            )

            if not result:
                return {"CANCELLED"}

            info = "%s added to %s list" % (
                act_coll.name,
                context.scene.cm.category.lower(),
            )
            self.report({"INFO"}, info)

        return {"FINISHED"}


class CM_OT_import_colls_from_config(bpy.types.Operator):
    """Move items up and down, add and remove"""

    bl_idname = "cm.import_colls_from_config"
    bl_label = "Import Collections"
    bl_description = "Import Colletions from Cacheconfig"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.scene.cm.use_cacheconfig_custom:
            return bool(
                context.scene.cm.is_cacheconfig_custom_valid
                and context.scene.cm.cacheconfig_custom_path.exists()
            )

        return bool(
            context.scene.cm.is_cacheconfig_valid
            and context.scene.cm.cacheconfig_path.exists()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cacheconfig_path = context.scene.cm.cacheconfig_path

        if context.scene.cm.use_cacheconfig_custom:
            cacheconfig_path = context.scene.cm.cacheconfig_custom_path

        log_new_lines(1)
        logger.info("-START- Importing Collections from Cacheconfig")

        cacheconfig = CacheConfigFactory.load_config_from_file(cacheconfig_path)
        colls = CacheConfigProcessor.import_collections(cacheconfig, context)

        self.report({"INFO"}, f"Imported {len(colls)} collections")
        log_new_lines(1)
        logger.info("-END- Importing Collections from Cacheconfig")

        return {"FINISHED"}


class CM_OT_update_cache_colls_list(bpy.types.Operator):

    bl_idname = "cm.udpate_cache_colls_list"
    bl_label = "Update Cache Collections List"
    bl_description = "Update cache collections list by scanning current scene for unadded cache collections"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        collections = list(opsdata.traverse_collection_tree(context.scene.collection))

        # clear any collections that got deleted
        propsdata.rm_deleted_colls_from_list(context)

        # search for cache collections that were not added
        for coll in collections:
            if not coll.cm.is_cache_coll:
                continue

            # should skip local colls if blend file not saved
            result = opsdata.add_coll_to_cache_collections(
                context, coll, context.scene.cm.category
            )
            if result:
                succeeded.append(coll)

        self.report({"INFO"}, f"Added {len(succeeded)} Collections to Cache List")
        log_new_lines(1)

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

        collection = context.scene.cm.colls_import[self.index].coll_ptr
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
        if context.scene.cm.use_cacheconfig_custom:
            return bool(
                context.scene.cm.is_cacheconfig_custom_valid
                and context.scene.cm.cacheconfig_custom_path.exists()
            )

        return bool(
            context.scene.cm.is_cacheconfig_valid
            and context.scene.cm.cacheconfig_path.exists()
        )

    def execute(self, context):
        log_new_lines(1)
        succeeded = []
        failed = []

        # cacheconfig path
        cacheconfig_path = context.scene.cm.cacheconfig_path
        if context.scene.cm.use_cacheconfig_custom:
            cacheconfig_path = context.scene.cm.cacheconfig_custom_path

        # clear deleted collections from list
        propsdata.rm_deleted_colls_from_list(context)

        # get collections to be processed
        if self.do_all:
            collections = list(props.get_cache_collections_import(context))
        else:
            collections = [context.scene.cm.colls_import[self.index].coll_ptr]

        # skip if  no cachefile assigned
        valid_colls = []
        for coll in collections:
            if not coll.cm.cachefile:
                failed.append(coll)
                logger.warning("%s has no cachefile assigned. Skip.", coll.name)
                continue
            valid_colls.append(coll)

        collections = valid_colls

        # log collections
        logger.info(
            "-START- Importing Cache for %s", ", ".join([c.name for c in collections])
        )

        # load animation data from config #disables drivers #TODO: driver disabling should happen here
        cacheconfig = CacheConfigFactory.load_config_from_file(cacheconfig_path)
        CacheConfigProcessor.import_animation_data(cacheconfig, collections)

        logger.info("-START- Importing Alembic Cache")

        # begin progress udpate
        context.window_manager.progress_begin(0, len(collections))

        # load alembic as mesh sequence cache
        for idx, coll in enumerate(collections):

            # log
            context.window_manager.progress_update(idx)
            log_new_lines(2)
            logger.info("%s", gen_processing_string(coll.name))

            # ensure cachefile is loaded or reloaded
            cachefile = opsdata.ensure_cachefile(coll.cm.cachefile)

            # get list with valid objects to apply cache to
            object_list = cache.get_valid_cache_objects(coll)

            # mute drivers
            muted_vis_drivers = opsdata.disable_vis_drivers(object_list, modifiers=True)

            # add cache modifier and constraints
            for obj in object_list:

                # get abc obj path
                abc_obj_path = cacheconfig.get_abc_obj_path(obj.name)

                # skip object if not found in cacheconfig
                if not abc_obj_path:
                    # abc_obj_paht = ""
                    continue

                # ensure and config constraint (can happen for mesh, empty, lattice, camera)
                con = opsdata.ensure_cache_constraint(obj)
                opsdata.config_cache_constraint(context, con, cachefile, abc_obj_path)

                # disable constraints
                opsdata.disable_non_keep_constraints(obj)

                # mesh sequence cache modifier configuration only for mesh objects
                if obj.type == "MESH":

                    # disable all armature modifiers, get index of first one, use that index for cache modifier
                    a_index = opsdata.disable_non_keep_modifiers(obj)
                    modifier_index = a_index if a_index != -1 else 0

                    # ensure and config cache modifier
                    mod = opsdata.ensure_cache_modifier(obj)
                    opsdata.config_cache_modifier(
                        context,
                        mod,
                        modifier_index,
                        cachefile,
                        abc_obj_path,
                    )
                # special case lattice needs mods disabled but cant have mesh sequence cash mod
                if obj.type == "LATTICE":
                    opsdata.disable_non_keep_modifiers(obj)

            # ensure MODIFIERS_KEEP are enabled after import
            # does not change viewport setting on enable
            opsdata.config_modifiers_keep_state(object_list, enable=True)

            # apply modifier suffix visibily override
            opsdata.apply_modifier_suffix_vis_override(object_list, "IMPORT")

            # set is_cache_loaded property
            coll.cm.is_cache_loaded = True

            logger.info("%s imported cache %s", coll.name, cachefile.filepath)
            succeeded.append(coll)

        # end progress update
        context.window_manager.progress_update(len(collections))
        context.window_manager.progress_end()

        log_new_lines(1)
        logger.info("-END- Importing Alembic Cache")

        # if it was do all reset after
        if self.do_all:
            self.do_all = False

        # log
        self.report(
            {"INFO"},
            f"Importing Cache for {len(succeeded)} Collections | Failed: {len(failed)}.",
        )
        log_new_lines(1)
        logger.info(
            "-END- Importing Cache for %s", ", ".join([c.name for c in collections])
        )
        return {"FINISHED"}


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
            collections = [context.scene.cm.colls_import[self.index].coll_ptr]

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

        # if it was do all hide reset after
        if self.do_all:
            self.do_all = False

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
            collections = [context.scene.cm.colls_import[self.index].coll_ptr]

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

        # if it was do all hide reset after
        if self.do_all:
            self.do_all = False

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
            collections = [context.scene.cm.colls_import[self.index].coll_ptr]

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

        # if it was do all hide reset after
        if self.do_all:
            self.do_all = False

        self.report(
            {"INFO"},
            f"Removed Cache of {len(collections)} Collections",
        )

        logger.info("-END- Removing Cache")
        return {"FINISHED"}


class CM_OT_set_cache_version(bpy.types.Operator):
    """"""

    bl_idname = "cm.set_cache_version"
    bl_label = "Version"
    # bl_options = {"REGISTER", "UNDO"}
    bl_property = "versions"

    versions: bpy.props.EnumProperty(
        items=opsdata.get_versions_enum_list, name="Versions"
    )

    index: bpy.props.IntProperty(name="Index")
    do_all: bpy.props.BoolProperty(
        name="Process All", description="Process all cache collections", default=True
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:

        if not context.scene.cm.is_cache_version_dir_valid:
            return False

        if context.scene.cm.category == "EXPORT":
            return True
        else:
            return not context.scene.cm.use_cacheconfig_custom

    def execute(self, context: bpy.types.Context) -> Set[str]:
        version = self.versions

        if not version:
            return {"CANCELLED"}

        if context.scene.cm.cache_version == version:
            return {"CANCELLED"}

        log_new_lines(1)
        # update global scene cache version prop
        context.scene.cm.cache_version = version
        logger.info("Set cache version to %s", version)

        if context.scene.cm.category == "IMPORT":
            # get collections to be processed
            if self.do_all:
                collections = list(props.get_cache_collections_import(context))
            else:
                collections = [context.scene.cm.colls_import[self.index].coll_ptr]

            # load cacheconfig
            cacheconfig_path = Path(context.scene.cm.cacheconfig_path)
            if not cacheconfig_path.exists():
                logger.error(
                    "Failed to load animation data. Cacheconfig does not exist: %s",
                    cacheconfig_path.as_posix(),
                )
            else:
                cacheconfig = CacheConfigFactory.load_config_from_file(cacheconfig_path)

            # process collections
            for coll in collections:
                if not coll.cm.cachefile:
                    logger.info("Ignored %s. No cachefile assigned yet.", coll.name)
                    continue

                # get old cachefile path and version
                cachefile_path_old = Path(coll.cm.cachefile)
                vers_old = opsdata.get_version(cachefile_path_old.name)

                if not vers_old:
                    logger.info(
                        "Failed to replace version: %s. No version pattern found.",
                        cachefile_path_old.name,
                    )
                    continue

                # gen new cachefile path with version that was selected
                cachefile_path_new = Path(
                    cachefile_path_old.as_posix().replace(vers_old, version)
                )

                if not cachefile_path_new.exists():
                    logger.info(
                        "%s (%s) failed to change version: %s > %s. Path with new version does not exist.",
                        coll.name,
                        cachefile_path_old.name,
                        vers_old,
                        version,
                    )
                    continue

                # try to get actual cachefile data block, catch key error if cachefile datablock not existent yet
                try:
                    cachefile = bpy.data.cache_files[cachefile_path_old.name]
                # do nothing
                except KeyError:
                    logger.error(
                        "%s assigned cachefile: %s is not imported. Skip changing cachefile path.",
                        coll.name,
                        cachefile_path_old.name,
                    )
                # if cachefile data block exists, update it to new version and import animation data
                # of cacheconfig with that version
                else:
                    # change cachefile filepath and name of cachefile datablock
                    cachefile.filepath = cachefile_path_new.as_posix()
                    cachefile.name = cachefile_path_new.name
                    logger.info(
                        "Changed cachefile path:\n %s > %s",
                        cachefile_path_old.as_posix(),
                        cachefile_path_new.as_posix(),
                    )

                    # import animation data from other cacheconfig
                    CacheConfigProcessor.import_animation_data(cacheconfig, [coll])
                    logger.info(
                        "%s loaded animation data from cacheconfig: %s",
                        coll.name,
                        cacheconfig_path,
                    )

                # either way update the cachefile prop of the collection (we know it exists here)
                finally:
                    coll.cm.cachefile = cachefile_path_new.as_posix()
                    logger.info(
                        "%s assign cachefile: %s",
                        coll.name,
                        cachefile_path_new.as_posix(),
                    )

        # redraw ui
        ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class CM_OT_add_cache_version_increment(bpy.types.Operator):
    """"""

    bl_idname = "cm.add_cache_version_increment"
    bl_label = "Add Version Increment"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # incremenet version
        version = opsdata.add_version_increment()

        # update cache_version prop
        context.scene.cm.cache_version = version

        ui_redraw()

        self.report({"INFO"}, f"Add version {version}")
        return {"FINISHED"}


# ---------REGISTER ----------

classes: List[Any] = [
    CM_OT_cache_export,
    CM_OT_cacheconfig_export,
    CM_OT_import_cache,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
    CM_OT_cache_show,
    CM_OT_cache_hide,
    CM_OT_cache_remove,
    CM_OT_import_colls_from_config,
    CM_OT_update_cache_colls_list,
    CM_OT_set_cache_version,
    CM_OT_add_cache_version_increment,
]


@persistent
def post_load_handler_update_cache_colls_list(dummy: Any) -> None:
    bpy.ops.cm.udpate_cache_colls_list()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # handlers
    bpy.app.handlers.load_post.append(post_load_handler_update_cache_colls_list)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # clear handlers
    bpy.app.handlers.load_post.remove(post_load_handler_update_cache_colls_list)
