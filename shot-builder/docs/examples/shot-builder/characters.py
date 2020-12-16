class Asset(shot_builder.some_module.Asset):
    asset_file = "/{asset_type}/{name}/{name}.blend"
    collection = "{class_name}"
    name = "{class_name}"


class Character(Asset):
    asset_type = 'char'


class Ellie(Character):
    collection = "{class_name}-{variant_name}"
    variants = {'default', 'short_hair'}


class Victoria(Character): pass
class Rex(Character): pass
