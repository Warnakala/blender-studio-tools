from shot_builder.asset import Asset


class SpriteFrightAsset(Asset):
    path = "{production.path}/lib/{asset.asset_type}/{asset.code}/{asset.code}.blend"


class Character(SpriteFrightAsset):
    asset_type = "char"
    collection = "CH-{asset.code}"


class Ellie(Character):
    name = "Ellie"
    code = "ellie"


class Victoria(Character):
    name = "Victoria"
    code = "victoria"


class Phil(Character):
    name = "Phil"
    code = "phil"


class Rex(Character):
    name = "Rex"
    code = "rex"


class Jay(Character):
    name = "Jay"
    code = "jay"

# TODO: Bird character has no asset file yet.
# class Bird(Character):
#     name = "Bird"
#     code = "bird"


class Prop(SpriteFrightAsset):
    asset_type = "props"
    collection = "PR-{asset.code}"


class Boombox(Prop):
    name = "Boombox"
    code = "boombox"


class BBQGrill(Prop):
    name = "BBQ Grill"
    code = "bbq_grill"


# TODO: NotepadAndPencil are stored in a single asset file, and have 2 separate collections.
# Need to ask how this one should be handled.
# class NotepadAndPencil(Prop):
#     name = "Notepad and pencil"
#     code = "notepad_pencil"


class Binoculars(Prop):
    name = "Binoculars (Ellie)"
    code = "binoculars"


class Backpack(Prop):
    name = "Backpack (Phil)"
    code = "backpack"


class Set(SpriteFrightAsset):
    asset_type = "sets"
    collection = "SE-{asset.code}"


class MushroomGrove(Set):
    name = "Mushroom grove"
    code = "mushroom_grove"
