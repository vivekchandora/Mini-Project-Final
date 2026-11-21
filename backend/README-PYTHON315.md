# Python 3.15 dependency note

Poupscan uses Shapely for geometry validation and pyproj for accurate area measurement.
On Windows, pyproj requires compiled PROJ binaries. The requirements file includes the
Geospatial Wheels Index as an additional package source and forces binary wheels for
pyproj and Shapely so pip does not attempt a local PROJ/source build.

Install from `backend` with:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the selected Python build/architecture has no matching wheel, pip will stop with a
clear no-compatible-wheel error instead of attempting a native PROJ compilation.
