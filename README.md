# CSL2XSB
Converts CSL packages to the original XSB format for use in [LiveTraffic](https://twinfan.gitbook.io/livetraffic/) (and probably XSquawkBox).
Currently only tested with the following providers:

- [X-CSL](https://csl.x-air.ru/?lang_id=43)

More probably to come with future versions.

As this is a Python 3 script you [need Python 3](https://www.python.org/downloads/).
Tested with Python 3.7.3.

## Synopsis

```
usage: CSL2XSB.py [-h] [--noupdate] [--norecursion] [-v] path

Convert CSL packages to original XSB format. Tested with: X-CSL.

positional arguments:
  path           Base path, searched recursively for CSL packages identified
                 by existing xsb_aircraft.txt files

optional arguments:
  -h, --help     show this help message and exit
  --noupdate     Suppress update of OBJ8 files if there are no additional
                 textures
  --norecursion  Do not search directories recursively
  -v, --verbose  More detailed output about every change
```

This will likely produce many new files, especially new `.OBJ` files, so disk usgae increases.

## Background

The format of CSL packages has originally been defined with the creation of the [libxplanemp library](https://github.com/kuroneko/libxplanemp/wiki). Since then, various dialects evolved, e.g. in X-IvAp or PilotEdge or the like. That means that CSL packages created for these clients cannot to their full extend be used in LiveTraffic, which uses the original format. There are disputes about how future-proof each format is.

To make other packages accessible to LiveTraffic (and likely, though not tested: XSquawkBox) this Python script `CSL2XSB.py` converts their format.

This only works for the OBJ8 format, which, however, is nowadays common.

## Package-specific Information

### X-CSL

X-CSL packages can be downloaded [here](https://csl.x-air.ru/downloads?lang_id=43). If you don't already have the package (e.g. because you use X-IvAp) then download and start the installer. The installer will _not_ identify LiveTraffic as a supported plugin. Instead, from the menu select `File > Select Custom Path` and specify a path where the CSL packages are to be downloaded to and where they later can be updated. 

Do not let `CSL2XSB.py` run on this original download. Always make a copy of the entire folder into a folder LiveTraffic can reach, e.g. to `<...>/LiveTraffic/Resources/X-CSL`. No run the script on this copy, e.g. like this:
```
python3 CSL2XSB.py <...>/LiveTraffic/Resources/X-CSL
```
You can always repeat the above call and the script shall do it just again (e.g. in case you modified any files manually). It keeps copies of original files that it needs for a repeated run.

What the script then does is, in brief, as follows:
1. It searches for `xsb_aircraft.txt` files. If it does not find any in the current directory it will recursively dig deeper into the folder structure. So it will eventually find all folders below `X-CSL`.
2. It copies the `xsb_aircraft.txt` file to `xsb_aircraft.txt.orig` and reads that to create a new `xsb_aircraft.txt` file.
3. **The `OBJ8 SOLID/LIGHTS` lines are at the core:** Here, additional parameters often define the texture files to use. The original format does not support these texture parameters. Instead, the textures are to be defined in the `.OBJ` file.
    - To remedy this, the script now also reads the `.OBJ` file and writes a _new_ version of it replacing the `TEXTURE` and `TEXTURE_LIT` lines.
    - This new `.OBJ` file is then referred to in the `OBJ8 SOLID/LIGHTS` line in the output version of `xsb_aircraft.txt`.
    - The availability of the referred texture and lit-texture files is tested. Some of them do not exist in the package, which causes warnings by the script. This is a problem in the original X-CSL package. In a few cases, the script can find a replacement by just replacing the extension of the texture file.
4. The script makes sure, that there is always a standard version of each aircraft type, identified by the `ICAO` line, so that at least some model/livery combination will be found and used by LiveTraffic, even if no exact airline match is possible.
5. Also, the script makes sure, that for each model/airline combination there is a default airline livery defined using the `AIRLINE` line. X-CSL sometimes provides several liveries for one airline (using `LIVERY` lines). But in the real world of LiveTraffic there is no way of identifying which aircraft uses which of these liveries, which often are just named arbitrarily `S`, `S1`, `S2`, and so on. This change makes sure that the first livery defined per airline is at least found and used. The other liveries are inaccessible to LiveTraffic at the moment.
6. Minor other changes:
    - Replace the non-existing ICAO aircraft designator `MD80` with `MD81`.
    - Remove deprecated lines like `OBJ8 GLASS/LOW_LOD` from `xsb_aircraft.txt`
    - Replace `:` or spaces in `OBJ8` aircraft names with `_`.

The size of the complete X-CSL package increases from about 2 GB to about 3.2 GB due to the additionally created `.OBJ` files.

The resulting folder structures and its files should be usable by LiveTraffic and produce no more warnings (except currently for one issue of `valid OBJ8 part types are LIGHTS or SOLID.  Got LIGHTS.`, which is a bug in libxplanemp and fixed with the next version, see [LiveTraffic issue 131](https://github.com/TwinFan/LiveTraffic/issues/131) to be shipped with v1.20).

See LiveTraffic's [documentation on CSL settings](https://twinfan.gitbook.io/livetraffic/setup/configuration/settings-csl) for how to provide LiveTraffic with the path to the converted X-CSL package.
