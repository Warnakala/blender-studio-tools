import bpy
from typing import List, Any, Set, cast
from pathlib import Path

from .logger import LoggerFactory
from . import blend, prefs

logger = LoggerFactory.getLogger(__name__)

VALID_OBJECT_TYPES = {"MESH"}


class CM_OT_cache_export(bpy.types.Operator):
    """"""

    bl_idname = "cm.cache_export"
    bl_label = "Export Cache"
    bl_description = "Exports alembic cache for selected collections"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return [context.scene.collection] and prefs.is_cachedir_valid(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        succeeded = []
        failed = []
        logger.info("-START- Exporting Cache")
        # already of type Path, convenience auto complete
        cachedir_path = Path(addon_prefs.cachedir_path)
        sel_cols = self._get_collections(context)

        # begin progress udpate
        context.window_manager.progress_begin(0, len(sel_cols))

        for idx, col in enumerate(sel_cols):
            context.window_manager.progress_update(idx)
            # identifier if col is valid?

            # deselect all
            bpy.ops.object.select_all(action="DESELECT")

            # create selection for alembic_export operator
            for obj in col.all_objects:
                if obj.type in VALID_OBJECT_TYPES and obj.name.startswith("GEO"):
                    logger.info("Valid object: %s", obj.name)
                    obj.select_set(True)

            filepath = cachedir_path / blend.gen_filename_collection(col)

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
                    flatten=False,
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
                logger.info("Failed to export %s", col.name)
                logger.exception(str(e))
                failed.append(col)
                continue

            succeeded.append(col)
            logger.info("Exported %s to %s", col.name, filepath.as_posix())

        # end progress update
        context.window_manager.progress_update(len(sel_cols))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Exported {len(succeeded)} Collections | Failed: {len(failed)}.",
        )

        logger.info("-END- Exporting Cache")
        return {"FINISHED"}

    def _get_collections(
        self, context: bpy.types.Context
    ) -> List[bpy.types.Collection]:
        return [context.view_layer.active_layer_collection.collection]


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


# ---------REGISTER ----------

classes: List[Any] = [CM_OT_cache_export, CM_OT_cache_list_actions]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
