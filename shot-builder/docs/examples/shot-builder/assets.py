from shot_builder.asset import AssetConfig


class Character(AssetConfig):
    path = "{production.path}/lib/char/{asset.config.asset_code}/{asset.config.asset_code}.blend"
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
