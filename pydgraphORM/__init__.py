import sys
import os.path as path
from .structure import (
    client_structure,
    flags_structure,
    model_structure,
)

__version__ = "0.1"

__title__ = "pydgraphORM"
__description__ = "ORM for pydgraph"
__uri__ = "https://github.com/SpreadPost/pydgraphORM/"
__doc__ = __description__ + " <" + __uri__ + ">"

__author__ = "David Ziegler"
__email__ = "development@SpreadPost.de"

__license__ = "Apache License 2.0"
__copyright__ = "Copyright (c) 2017 David Ziegler"

__path__.append(path.join(path.dirname(__file__), "structure"))

__all__ = [
    "client_structure",
    "flags_structure",
    "model_structure",
]

if sys.version_info[:2][0] == 2:
    warnings.warn(
        "Python 2 is no longer supported by pydgraphORM, please "
        "upgrade your Pytho to Version 3.x"
    )

