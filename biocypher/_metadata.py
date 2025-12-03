"""
Package metadata (version, authors, etc).
"""

__all__ = ["get_metadata"]

import importlib.metadata
import os
import pathlib

try:
    import toml
except ImportError:
    toml = None

_VERSION = "0.12.0"


def get_metadata():
    """
    Basic package metadata.

    Retrieves package metadata from the current project directory or from
    the installed package.
    """

    here = pathlib.Path(__file__).parent
    pyproj_toml = "pyproject.toml"
    meta = {}

    for project_dir in (here, here.parent):
        toml_path = str(project_dir.joinpath(pyproj_toml).absolute())

        if os.path.exists(toml_path) and toml is not None:
            try:
                pyproject = toml.load(toml_path)
            except Exception:
                # If toml parsing fails, skip and use fallback
                continue

            # Use modern PEP 621 format (uv/hatchling)
            if "project" in pyproject:
                project = pyproject["project"]
                meta = {
                    "name": project.get("name"),
                    "version": project.get("version"),
                    "author": project.get("authors", []),
                    "license": project.get("license", {}).get("text"),
                    "full_metadata": pyproject,
                }
            elif "tool" in pyproject and "poetry" in pyproject["tool"]:
                # Legacy Poetry format fallback (for backward compatibility)
                poetry = pyproject["tool"]["poetry"]
                meta = {
                    "name": poetry.get("name"),
                    "version": poetry.get("version"),
                    "author": poetry.get("authors", []),
                    "license": poetry.get("license"),
                    "full_metadata": pyproject,
                }

            break

    if not meta:
        try:
            meta = {k.lower(): v for k, v in importlib.metadata.metadata(here.name).items()}

        except importlib.metadata.PackageNotFoundError:
            pass

    meta["version"] = meta.get("version", None) or _VERSION

    return meta


metadata = get_metadata()
__version__ = metadata.get("version", None)
__author__ = metadata.get("author", None)
__license__ = metadata.get("license", None)
