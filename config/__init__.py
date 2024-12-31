# __init__.py

import pathlib
import tomli

path = pathlib.Path(__file__).parent / "splunkapps.toml"
with path.open(mode="rb") as fp:
    splunkapps = tomli.load(fp)
