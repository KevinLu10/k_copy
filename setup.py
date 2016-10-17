# encoding=utf8
from distutils.core import setup
import py2exe

options = {"py2exe":
               {"compressed": 1,
                "optimize": 2,
                "bundle_files": 3,
                }
           }
setup(
    version="1.0.3",
    description="KCopy",
    name="KCopy",
    options=options,
    zipfile=None,
    data_files=[("",
                 [r"KCopyIcon.ico"]),
                ],
    windows=[{
        "script": "KCopyMain.py",
        "icon_resources": [(1, "KCopyIcon.ico")]
    }],
)
if __name__ == '__main__':
    pass
