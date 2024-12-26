# __init__.py

import pathlib
import tomllib

path = pathlib.Path(__file__).parent / "splunkapps.toml"
with path.open(mode="rb") as fp:
    splunkapps = tomllib.load(fp)
