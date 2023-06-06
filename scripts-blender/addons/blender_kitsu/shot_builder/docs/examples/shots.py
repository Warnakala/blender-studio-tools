from blender_kitsu.shot_builder.shot import Shot
from blender_kitsu.shot_builder.project import Production


class SpriteFrightShot(Shot):
    def get_anim_file_path(self, production: Production, shot: Shot) -> str:
        """
        Get the animation file path for this given shot.
        """
        return self.file_path_format.format_map({
            'production': production,
            'shot': shot,
            'task_type': "anim"
        })

    def get_output_collection_name(self, shot: Shot, task_type: str) -> str:
        """
        Get the collection name where the output is stored.
        """
        return f"{shot.sequence_code}_{shot.code}.{task_type}.output"


class Sequence_0002(SpriteFrightShot):
    sequence_code = "0002"


class Shot_0001_0001_A(Sequence_0002):
    name = "001"
    code = "0001"
