# __init__.py

import pathlib
try: import tomllib
except ModuleNotFoundError: import pip._vendor.tomli as tomllib

path = pathlib.Path(__file__).parent / "splunkapps.toml"
with path.open(mode="rb") as fp:
    splunkapps = tomllib.load(fp)
