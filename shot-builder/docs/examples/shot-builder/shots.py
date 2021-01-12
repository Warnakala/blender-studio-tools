class Shot_01_020_A(shot_builder.some_module.Shot):
    shot_id = '01_020_A'
    assets = {
        characters.Ellie(variant=”short_hair”, location=(0.0, 0.0, 0.0)),
        characters.Rex,
        sets.LogOverChasm,
    }
    # Offset of all assets to reduce floating point errors.
    world_center = [1000, 0, 250]


class AllHumansShot(shot_builder.some_module.Shot):
    assets = {
        characters.Ellie(variant=”short_hair”),
        characters.Rex,
        characters.Victoria,
    }


class Shot_01_035_A(AllHumansShot):
    assets = {
        sets.Camp,
    }