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
# (c) 2021, Blender Foundation - Paul Golter
import importlib
import logging

from typing import List, Dict, Union, Any, Set, Optional
from types import ModuleType, FunctionType

from pathlib import Path

import bpy

from .task_layer import TaskLayer, TaskLayerAssembly
from .hook import Hooks

from .. import constants, prop_utils
from ..sys_utils import SystemPathInclude
from ..asset_files import AssetDir, AssetPublish, AssetTask

logger = logging.getLogger("BSP")


class ProdContextFailedToInitialize(Exception):
    pass


class AssetContextFailedToInitialize(Exception):
    pass


class BuildContextFailedToInitialize(Exception):
    pass


class InvalidTaskLayerDefinition(Exception):
    pass

class ProcessPair:
    """
    Simple Class that stores a logically connected target and a pull from path.
    """

    def __init__(self, asset_task: AssetTask, asset_publish: AssetPublish) -> None:
        self.asset_task = asset_task
        self.asset_publish = asset_publish

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProcessPair):
            raise NotImplementedError()

        return bool(
            self.asset_task == other.asset_task
            and self.asset_publish == other.asset_publish
        )

    def __hash__(self) -> int:
        return hash((self.asset_task, self.asset_publish))


class ProductionContext:

    """
    A context that represents configuration on a Production Level.
    Independent from Blender, no bpy access.
    """

    def __init__(self, config_folder: Path):

        if not config_folder or not config_folder.exists():
            raise ProdContextFailedToInitialize(
                f"Failed to init ProductionContext. Invalid config folder: {config_folder}"
            )

        self._task_layers: List[type[TaskLayer]] = []
        self._transfer_settings: Optional[type[bpy.types.PropertyGroup]] = None
        self._config_folder: Path = config_folder
        self._module_of_task_layers: Optional[ModuleType] = None
        self._module_of_hooks: Optional[ModuleType] = None
        self._hooks = Hooks()

        # Load configs from config_folder.
        self._collect_configs()
        logger.debug("Initialized Production Context")

    @property
    def config_folder(self) -> Path:
        return self._config_folder

    @property
    def task_layers(self) -> List[type[TaskLayer]]:
        return self._task_layers

    def get_task_layer_orders(self) -> List[int]:
        """
        Returns a list of all TaskLayers.order values.
        """
        return [t.order for t in self.task_layers]

    def _collect_configs(self) -> None:

        # Add config folder temporarily to sys.path for convenient
        # import.

        with SystemPathInclude([self._config_folder]):

            # Load Task Layers.
            # TODO: information duplicated in add-on preferences
            # Make it DRY

            # Check if task layers module was already imported.
            # TODO: does not work perfectly, if we remove a TaskLayer from
            # config file and then reload, it's still there.
            # https://stackoverflow.com/questions/2918898/prevent-python-from-caching-the-imported-modules
            if self._module_of_task_layers:
                # Reload it so Users won't have to restart Blender.
                self._module_of_task_layers = importlib.reload(
                    self._module_of_task_layers
                )
            else:
                import task_layers as prod_task_layers

                self._module_of_task_layers = prod_task_layers

            # TODO: add check exception handeling if hooks module not existent.
            import hooks

            self._module_of_hooks = hooks

            # Crawl module for TaskLayers.
            self._collect_prod_task_layers()
            self._collect_prod_hooks()
            self._collect_prod_transfer_settings()

    def _collect_prod_task_layers(self) -> None:

        # Clear task layer list, otherwise we will add new but don't
        # remove old.
        self._task_layers.clear()
        module = self._module_of_task_layers

        # Find all valid TaskLayer Classes.
        for module_item_str in dir(module):
            module_item = getattr(module, module_item_str)

            # This checks that the module item is a class definition
            # and not e.G and instance of that class.
            if module_item.__class__ != type:
                continue

            if not issubclass(module_item, TaskLayer):
                continue

            # We don't want to collect to Root TaskLayer class.
            # Only classes that inherit from it.
            if module_item == TaskLayer:
                continue

            # Checks e.G that 'name' class attribute is set.
            if not module_item.is_valid():
                if module_item.order < 0:
                    raise InvalidTaskLayerDefinition(
                        f"Invalid TaskLayer {str(module_item)} Order attribute not set.",
                    )
                if not module_item.name:
                    raise InvalidTaskLayerDefinition(
                        f"Invalid Task Layer {str(module_item)} Name attribute not set.",
                    )
                continue

            self._task_layers.append(module_item)

        # Check if any TaskLayers have the same order.
        self._validate_task_layer_orders()

        # Sort TaskLayers after order attribute.
        self._task_layers.sort(key=lambda tl: tl.order)

        if self.task_layers:
            logger.info(f"Detected Production TaskLayers: {self.task_layers}")

    def _collect_prod_hooks(self) -> None:

        module = self._module_of_hooks
        self._hooks = Hooks()

        for module_item_str in dir(module):
            module_item = getattr(module, module_item_str)
            # Skip non functions.
            if not isinstance(module_item, FunctionType):
                continue
            # Skip functions of other modules.
            if module_item.__module__ != module.__name__:
                continue
            # @hook() decorator adds this attribute which make a hook
            # distinguishable from a regular function.
            # Note: @hook() needs to be called otherwise this check
            # will fail.
            if not hasattr(module_item, constants.HOOK_ATTR_NAME):
                continue

            self._hooks.register(module_item)

        if self._hooks:
            logger.info(f"Detected Production Hooks: {self._hooks.callables}")

    def _collect_prod_transfer_settings(self) -> None:
        """
        Here we search the task_layers.py module for a class that is
        named as defined in constants.TRANSFER_SETTINGS_NAME. This is supposed to be
        a regular Blender PropertyGroup. In this PropertyGroup Users can define
        regular blender Properties that represent a setting to customize the
        transfer data process. This PropertyGroup will be registered on scene level
        and can then be easily queried in the transfer data function of the TaskLayer.
        That way Users can provide themselves options to use in their code.
        This options are also displayed in the Blender AssetPipeline Panel automatically.
        """
        self._transfer_settings = None
        module = self._module_of_task_layers

        try:
            prop_group = getattr(module, constants.TRANSFER_SETTINGS_NAME)
        except AttributeError:
            logger.info(
                "No Transfer Settings loaded. Failed to find %s variable.",
                constants.TRANSFER_SETTINGS_NAME,
            )
        else:
            # Check if prop group is actually of type PropertyGroup.
            if not issubclass(prop_group, bpy.types.PropertyGroup):
                raise ProdContextFailedToInitialize(
                    f"{constants.TRANSFER_SETTINGS_NAME} must be subclass of bpy.types.PropertyGroup"
                )
            self._transfer_settings = prop_group
            try:
                bpy.utils.unregister_class(prop_group)
            except RuntimeError:
                bpy.utils.register_class(prop_group)
                # Scene Asset Pipeline Properties.
                bpy.types.Scene.bsp_asset_transfer_settings = bpy.props.PointerProperty(
                    type=prop_group
                )

            logger.info(f"Detected Transfer Settings: {self._transfer_settings}")
            logger.info(
                f"Registered Transfer Settings:  bpy.types.Scene.bsp_asset_transfer_settings"
            )

    def _validate_task_layer_orders(self) -> None:
        for i in range(len(self._task_layers)):
            tl = self._task_layers[i]

            for j in range(i + 1, len(self._task_layers)):
                tl_comp = self._task_layers[j]
                if tl.order == tl_comp.order:
                    raise InvalidTaskLayerDefinition(
                        f"Invalid Task Layer {str(tl)} has some 'order' as {str(tl_comp)}.",
                    )

    @property
    def hooks(self) -> Hooks:
        return self._hooks

    def __repr__(self) -> str:
        header = "\nPRODUCTION CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        prod_task_layers = (
            f"Production Task Layers: {[t.name for t in self._task_layers]}"
        )
        return "\n".join([header, prod_task_layers, footer])

    def __getstate__(self) -> Dict[str, Any]:
        # Pickle uses this function to generate a dictionary which it uses
        # to pickle the instance.
        # Here we can basically overwrite this dictionary, for example to
        # delete some properties that pickle can't handle.

        # Pickle cannot store module objects.
        state = self.__dict__.copy()
        state["_module_of_task_layers"] = None
        state["_module_of_hooks"] = None
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        # Pickle uses a state Dictionary to restore the instance attributes.
        # In this function we can overwrite this behavior and restore
        # data that pickle wasn't able to store

        self.__dict__.update(state)

        # Restore module object.
        with SystemPathInclude([self.config_folder]):
            import task_layers as prod_task_layers
            import hooks

            self._module_of_task_layers = prod_task_layers
            self._module_of_hooks = hooks


class AssetContext:

    """
    Should be updated on each scene load.
    """

    def __init__(self, bl_context: bpy.types.Context, prod_context: ProductionContext):

        # Check if bl_context and config_folder are valid.
        if not all([bl_context, bl_context.scene.bsp_asset.asset_collection]):
            raise AssetContextFailedToInitialize(
                "Failed to initialize AssetContext. Invalid blender_context or asset collection not set."
            )
        # Check if file is saved.
        if not bpy.data.filepath:
            raise AssetContextFailedToInitialize(
                "Failed to initialize AssetContext. File not saved"
            )

        self._bl_context: bpy.types.Context = bl_context
        self._asset_collection: bpy.types.Collection = (
            bl_context.scene.bsp_asset.asset_collection
        )
        self._task_layer_assembly = TaskLayerAssembly(prod_context._task_layers)
        self._asset_dir = AssetDir(Path(bpy.data.filepath).parent)
        self._asset_task = AssetTask(Path(bpy.data.filepath))
        self._asset_publishes: List[
            AssetPublish
        ] = []  # TODO: could convert in to  set.

        # Transfer settings are stored in a PropertyGroup on scene level.
        # We cannot pickle those. So what we do is write them in a dictionary here
        # before publish and restore the settings when we open the other blend file.
        self._transfer_settings: Dict[str, Any] = {}

        # TODO: Load custom Task Layers.
        self._custom_task_layers: List[Any] = []

        self._collect_asset_publishes()
        logger.debug("Initialized Asset Context")

    @property
    def asset_collection(self) -> bpy.types.Collection:
        return self._asset_collection

    @property
    def asset_name(self) -> str:
        return self.asset_collection.bsp_asset.entity_name

    @property
    def asset_task(self) -> AssetTask:
        return self._asset_task

    @property
    def asset_dir(self) -> AssetDir:
        return self._asset_dir

    @property
    def asset_publishes(self) -> List[AssetPublish]:
        return self._asset_publishes

    @property
    def task_layer_assembly(self) -> TaskLayerAssembly:
        return self._task_layer_assembly

    @property
    def transfer_settings(self) -> Dict[str, Any]:
        return self._transfer_settings

    def update_from_bl_context(self, bl_context: bpy.types.Context) -> None:
        self._bl_context = bl_context
        self._asset_collection = bl_context.scene.bsp_asset.asset_collection
        self._update_task_layer_assembly_from_context(bl_context)
        self._update_transfer_settings_from_context(bl_context)

    def reload_asset_publishes(self) -> None:
        self._collect_asset_publishes()

    def reload_asset_publishes_metadata(self) -> None:
        for asset_publish in self.asset_publishes:
            asset_publish.reload_metadata()

    def _collect_asset_publishes(self) -> None:
        self._asset_publishes.clear()
        self._asset_publishes.extend(self._asset_dir.get_asset_publishes())

    def _update_task_layer_assembly_from_context(
        self, bl_context: bpy.types.Context
    ) -> None:
        # Update TaskLayerAssembly, to load the
        # previously disabled and enabled TaskLayer States.
        # They are stored in context.scene.bl_asset.task_layers

        # TODO: we should take in to account that in the meantime
        # production TaskLayers could have been updated.
        for item in bl_context.scene.bsp_asset.task_layers:
            task_layer_config = self.task_layer_assembly.get_task_layer_config(
                item.task_layer_id
            )
            task_layer_config.use = item.use

    def _update_transfer_settings_from_context(
        self, bl_context: bpy.types.Context
    ) -> None:
        for prop_name, prop in prop_utils.get_property_group_items(
            bl_context.scene.bsp_asset_transfer_settings
        ):
            self._transfer_settings[prop_name] = getattr(
                bl_context.scene.bsp_asset_transfer_settings, prop_name
            )

    def __repr__(self) -> str:
        header = "\nASSET CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        asset_info = f"Asset: {self.asset_collection.bsp_asset.entity_name}({self.asset_collection})"
        task_layer_assembly = str(self.task_layer_assembly)

        return "\n".join(
            [
                header,
                asset_info,
                task_layer_assembly,
                footer,
            ]
        )

    def __getstate__(self) -> Dict[str, Any]:

        # Pickle cannot pickle blender context or collection.
        state = self.__dict__.copy()
        state["_bl_context"] = None
        state["_restore_asset_collection_name"] = self.asset_collection.name
        state["_asset_collection"] = None
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        asset_coll_name = state["_restore_asset_collection_name"]
        asset_coll = bpy.data.collections[asset_coll_name]
        self._asset_collection = asset_coll
        self._bl_context = bpy.context

        del self._restore_asset_collection_name
        logger.info(
            "Restored Asset Collection: %s, Context: %s",
            str(self._asset_collection),
            str(self._bl_context),
        )


class BuildContext:

    """
    Class that should function as Context for the asset build.
    Here we want to store everything that is relevant for the build.
    The Builder will process this context.
    Should be updated on start publish/pull and only be relevant for publish/pull.
    """

    def __init__(
        self,
        prod_context: ProductionContext,
        asset_context: AssetContext,
    ):
        if not all([prod_context, asset_context]):
            raise BuildContextFailedToInitialize(
                "Failed to initialize Build Context. Production or Asset Context not initialized."
            )

        self._prod_context: ProductionContext = prod_context
        self._asset_context: AssetContext = asset_context
        self._process_pairs: Set[ProcessPair] = set()

        self._collect_process_pairs()

    def _collect_process_pairs(self) -> None:
        # Here we want to loop through all asset publishes and
        # create a list of process pairs out of it.
        # This is the place where we perform the logic of checking
        # which task layers the user selected in self._asset_context.task_layer_assembly
        # and then reading the metadata of each asset publish and check where the corresponding
        # task layers are live.
        # The result of this is a list of process pairs(target, pull_from) that
        # the AssetBuilder needs to process
        self._process_pairs.clear()

        tl_assembly = self._asset_context.task_layer_assembly
        task_layers_enabled = tl_assembly.get_used_task_layers()

        for asset_publish in self.asset_publishes:

            # For this asset publish get all locked task layers IDs.
            locked_task_layer_ids = asset_publish.metadata.get_locked_task_layer_ids()

            # Check if there is any enabled Task Layer ID that is not in the locked IDs.
            for tl in task_layers_enabled:
                if tl.get_id() not in locked_task_layer_ids:
                    self._process_pairs.add(ProcessPair(self.asset_task, asset_publish))

    @property
    def prod_context(self) -> ProductionContext:
        return self._prod_context

    @property
    def asset_context(self) -> AssetContext:
        return self._asset_context

    @property
    def asset_task(self) -> AssetTask:
        return self.asset_context.asset_task

    @property
    def asset_dir(self) -> AssetDir:
        return self.asset_context.asset_dir

    @property
    def asset_publishes(self) -> List[AssetPublish]:
        return self.asset_context.asset_publishes

    @property
    def process_pairs(self) -> Set[ProcessPair]:
        return self._process_pairs

    def __repr__(self) -> str:
        header = "\nBUILD CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        asset_task = f"Asset Task: {str(self.asset_task)}"
        asset_disk_name = f"Asset Disk Name: {self.asset_dir.asset_disk_name}"
        asset_dir = f"Asset Dir: {str(self.asset_dir)}"
        return "\n".join(
            [
                header,
                asset_disk_name,
                asset_task,
                asset_dir,
                str(self.prod_context),
                str(self.asset_context),
                footer,
            ]
        )

    def get_hook_kwargs(self) -> Dict[str, Any]:
        return {
            "asset_collection": self.asset_context.asset_collection,
            "context": bpy.context,
            "asset_task": self.asset_task,
            "asset_dir": self.asset_context.asset_dir,
        }


class UndoContext:
    """
    This should be a context that we can populate along the way of starting a publish and actually publishing.
    The idea is that we can add 'undo' steps that we can then undo() if users aborts the publish.
    The point of it is to mainly be able to revert the filesystem and other things that happen between starting
    the publish and aborting it.
    These steps will also be mirrored on the scene Property group so you can actually start a publish
    open another scene and still abort it and it will undo the correct things.
    """

    def __init__(self):
        self._asset_publishes: List[AssetPublish] = []

    def add_step_publish_create(
        self, bl_context: bpy.types.Context, asset_publish: AssetPublish
    ) -> None:
        # Add to self context.
        self._asset_publishes.append(asset_publish)

        # Add to scene, to restore on load.
        bl_context.scene.bsp_asset.undo_context.add_step_asset_publish_create(
            asset_publish
        )

        logger.debug("Created file creation undo step: %s", asset_publish.path.name)

    def undo(self, bl_context: bpy.types.Context) -> None:

        # Delete files.
        for asset_publish in self._asset_publishes:
            if asset_publish.path.exists():
                logger.info(
                    "Undoing file creation. Delete: [%s, %s]",
                    asset_publish.path.name,
                    asset_publish.metadata_path.name,
                )
                asset_publish.unlink()

        # Clear self steps.
        self._asset_publishes.clear()

        # Clear scene.
        bl_context.scene.bsp_asset.undo_context.clear()

    def update_from_bl_context(self, bl_context: bpy.types.Context) -> None:

        self._asset_publishes.clear()

        for item in bl_context.scene.bsp_asset.undo_context.files_created:
            self._asset_publishes.append(AssetPublish(item.path))
