from shot_builder.asset import AssetConfig


class Asset(AssetConfig):
    path = "{production.path}/lib/{asset.config.asset_type}/{asset.config.asset_code}/{asset.config.asset_code}.blend"


class Character(Asset):
    asset_type = "char"
    collection = "CH-{asset.config.asset_code}"


class Ellie(Character):
    asset_name = "Ellie"
    asset_code = "ellie"


class Victoria(Character):
    asset_name = "Victoria"
    asset_code = "victoria"


class Phil(Character):
    asset_name = "Phil"
    asset_code = "phil"


class Rex(Character):
    asset_name = "Rex"
    asset_code = "rex"


class Jay(Character):
    asset_name = "Jay"
    asset_code = "jay"


# class Bird(Character):
#     asset_name = "Bird"
#     asset_code = "bird"


class Prop(Asset):
    asset_type = "props"
    collection = "PR-{asset.config.asset_code}"


class Boombox(Prop):
    asset_name = "Boombox"
    asset_code = "boombox"


class BBQGrill(Prop):
    asset_name = "BBQ Grill"
    asset_code = "bbq_grill"


class NotepadAndPencil(Prop):
    asset_name = "Notepad and pencil"
    asset_code = "notepad_pencil"


class Binoculars(Prop):
    asset_name = "Binoculars (Ellie)"
    asset_code = "binoculars"


class Backpack(Prop):
    asset_name = "Backpack (Phil)"
    asset_code = "backpack"


class Set(Asset):
    asset_type = "sets"
    collection = "SE-{asset.config.asset_code}"


class MushroomGrove(Set):
    asset_name = "Mushroom grove"
    asset_code = "mushroom_grove"
