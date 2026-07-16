try:
    import configobj  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module configobj; please install with command 'pip install configobj' or 'conda -y install configobj'. See https://configobj.readthedocs.io/en/latest/configobj.html#downloading for more information."
    )

try:
    import pandas  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module pandas; please install with command 'pip install pandas' or 'conda -y install pandas'. See http://pandas.pydata.org/pandas-docs/stable/install.html for more information."
    )

try:
    import networkx  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module networkx; please install with command 'pip install networkx' or 'conda -y install networkx'. See https://networkx.github.io/documentation/stable/install.html for more information."
    )

try:
    import pymysql  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module pymysql; please install with command 'pip install pymysql' or 'conda -y install pymysql'. See https://pymysql.readthedocs.io/en/latest/user/installation.html for more information."
    )

try:
    import lxml  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module lxml; please install with command 'pip install lxml' or 'conda -y install lxml'. See https://lxml.de/installation.html for more information."
    )

try:
    import numpy  # noqa: F401 -- availability probe only
except (ImportError, ImportWarning):
    print(
        "unable to load module numpy; please install with command 'pip install numpy' or 'conda -y install numpy'. See https://www.scipy.org/scipylib/download.html for more information."
    )
