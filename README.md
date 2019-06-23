# CSL2XSB
Converts CSL packages to the original XSB format for use in [LiveTraffic](https://twinfan.gitbook.io/livetraffic/) (and probably XSquawkBox). Updates some CSL dataRefs (engine/prop rotation, reversers) so they become available to LiveTraffic.
Currently only tested with the following providers:

- [Bluebell Package](https://forums.x-plane.org/index.php?/files/file/37041-bluebell-obj8-csl-packages/)
- [X-CSL](https://csl.x-air.ru/?lang_id=43)

More probably to come with future versions.

As this is a Python 3 script you [need Python 3](https://www.python.org/downloads/).
Tested with Python 3.7.3.

## Simple usage in Windows

- Install Python 3 using the "Windows x86-64 web-based installer" [direct link for v3.7.3](https://www.python.org/ftp/python/3.7.3/python-3.7.3-amd64-webinstall.exe).
    - Important: Check (select) the option "Add Python 3.7 to PATH" at the bottom of the "Install Python" window.
    - Click on "Install Now". Python will install.
    - When donw, click "Close" in the "Setup was successfull" screen. Now you've got Python 3.
- Download a CSL package like from X-CSL.
- Make a copy of it!
- Put the `CSL2XSB.py` script into the base directory of the that copy.
- Double-lick the `CSL2XSB.py` script in the explorer to start it. It will ask you if you want to run the script in that current directory. Enter "y" and hit Enter.
- It then asks "Do you want to replace dataRefs in the CSL...?" Read below about it in the section "Several multiplayer clients in parallel". If unsure leave this alone and just hit enter.

## Synopsis

```
usage: CSL2XSB.py [-h] [--noupdate] [--norecursion] [-v] [--replaceDR TEXT]
                  [path]

CSL2XSB 0.2.0: Convert CSL packages to original XSB format. Tested with:
X-CSL.

positional arguments:
  path              Base path, searched recursively for CSL packages
                    identified by existing xsb_aircraft.txt files

optional arguments:
  -h, --help        show this help message and exit
  --noupdate        Suppress update of OBJ8 files if there are no additional
                    textures
  --norecursion     Do not search directories recursively
  -v, --verbose     More detailed output about every change
  --replaceDR TEXT  Replace dataRef's root 'libxplanemp' with TEXT. CAUTION:
                    CSLs' animations/lights will no longer work with standard
                    multipayer clients not supporting modified dataRefs!
```

This will likely produce many new files, especially new `.OBJ` files, so disk usage increases.

## Background

The format of CSL packages has originally been defined with the creation of the [libxplanemp library](https://github.com/kuroneko/libxplanemp/wiki). Since then, various dialects evolved, e.g. in X-IvAp or PilotEdge or the like. That means that CSL packages created for these clients cannot to their full extend be used in LiveTraffic, which uses the original format. There are disputes about how future-proof each format is.

To make other packages accessible to LiveTraffic (and likely, though not tested: XSquawkBox) this Python script `CSL2XSB.py` converts their format.

This only works for the OBJ8 format, which, however, is nowadays common.

### Using several multiplayer clients in parallel - replacing root dataRef string

Several multiplayer clients based on `libxplanemp` can in principle run in parallel. But it is the library, which registers the [CSL dataRefs for animations/lights](https://github.com/kuroneko/libxplanemp/wiki/OBJ8-CSL#animations), by which the objects (read: planes) learn about gear/flap extension ratio, lights etc. There can only be one plugin, which can control gear/flap/lights etc. of its AI planes. The others fail to register the CSL dataRefs and cannot control these details of their planes.

LiveTraffic implements a temporariy workaround for the situation: It offers to change these dataRefs, which usually all start with the text `libxplanemp/` to start with `LT/` instead. For this to work also all CSL objects, i.e. the `.obj` files need to be changed to also use the `LT/` dataRef.

`CSL2XSB` offers to perform this change mit the `--replaceDR` option. On the command line you can enter any string. With LiveTraffic, only `LT` will work. The interactive version (see "Simple Usage in Windows" above) only asks _if_ the user wants to have it replaced and replaces it with `LT`.

**Note:** CSL package converted to a different dataRef root can no longer be used with any other client. This copy will only work with LiveTraffic and only if the root string is `LT`.

## Package-specific Information

### X-CSL

X-CSL packages can be downloaded [here](https://csl.x-air.ru/downloads?lang_id=43). If you don't already have the package (e.g. because you use X-IvAp) then download and start the installer. The installer will _not_ identify LiveTraffic as a supported plugin. Instead, from the menu select `File > Select Custom Path` and specify a path where the CSL packages are to be downloaded to and where they later can be updated. 

Do not let `CSL2XSB.py` run on this original download. Always make a copy of the entire folder into a folder LiveTraffic can reach, e.g. to `<...>/LiveTraffic/Resources/X-CSL`. Now run the script on this copy, e.g. like this:
```
python CSL2XSB.py <...>/LiveTraffic/Resources/X-CSL
```
(Note that in some environments like Mac OS you need to specifically call `python3` instead of just `python`.)

You can always repeat the above call and the script shall do it just again (e.g. in case you modified any files manually). It keeps copies of original files that it needs for a repeated run.

What the script then does is, in brief, as follows:
1. It searches for `xsb_aircraft.txt` files. If it does not find any in the current directory it will recursively dig deeper into the folder structure. So it will eventually find all folders below `X-CSL`.
2. It copies the `xsb_aircraft.txt` file to `xsb_aircraft.txt.orig` and reads that to create a new `xsb_aircraft.txt` file.
3. **The `OBJ8 SOLID/LIGHTS/GLASS` lines are at the core:** Here, additional parameters often define the texture files to use. The original format does not support these texture parameters. Instead, the textures are to be defined in the `.OBJ` file.
    - To remedy this, the script now also reads the `.OBJ` file and writes a _new_ version of it replacing the `TEXTURE` and `TEXTURE_LIT` lines.
    - This new `.OBJ` file is then referred to in the `OBJ8 SOLID/LIGHTS` line in the output version of `xsb_aircraft.txt`. (An original `OBJ8 GLASS` line will be written to output as `OBJ8 SOLID` as `GLASS` is now deprecated.)
    - The availability of the referred texture and lit-texture files is tested. Some of them do not exist in the package, which causes warnings by the script. This is a problem in the original X-CSL package. In a few cases, the script can find a replacement by just replacing the extension of the texture file.
4. The script makes sure, that there is always a standard version of each aircraft type, identified by the `ICAO` line, so that at least some model/livery combination will be found and used by LiveTraffic, even if no exact airline match is possible.
5. Also, the script makes sure, that for each model/airline combination there is a default airline livery defined using the `AIRLINE` line. X-CSL sometimes provides several liveries for one airline (using `LIVERY` lines). But in the real world of LiveTraffic there is no way of identifying which aircraft uses which of these liveries, which often are just named arbitrarily `S`, `S1`, `S2`, and so on. This change makes sure that the first livery defined per airline is at least found and used. The other liveries are inaccessible to LiveTraffic at the moment.
6. Minor other changes:
    - Replace the non-existing ICAO aircraft designator `MD80` with `MD81`.
    - Remove deprecated lines like `LOW_LOD` from `xsb_aircraft.txt`
    - Replace `:` or spaces in `OBJ8` aircraft names with `_`.

The size of the complete X-CSL package increases from about 2 GB to about 3.2 GB due to the additionally created `.OBJ` files.

The resulting folder structures and its files should be usable by LiveTraffic and produce no more warnings (except currently for one issue of `valid OBJ8 part types are LIGHTS or SOLID.  Got LIGHTS.`, which is a bug in libxplanemp and fixed with the next version, see [LiveTraffic issue 131](https://github.com/TwinFan/LiveTraffic/issues/131) to be shipped with v1.20).

See LiveTraffic's [documentation on CSL settings](https://twinfan.gitbook.io/livetraffic/setup/configuration/settings-csl) for how to provide LiveTraffic with the path to the converted X-CSL package.

### Bluebell

The Bluebell package is the standard package recommended for usage with LiveTraffic. Many CSL object in the Bluebell package are capable of turning rotors or open reversers. But as there was no `libxplanemp` CSL dataRef to control these animation they stayed unchanged in the `.obj` files, e.g. like `cjs/world_traffic/engine_rotation_angle1`.

LiveTraffic now implements more CSL dataRefs than in the standard `libxplanemp` version, e.g. for engine/prop rotation and reversers animation, and tries to stick to a [standard set by PilotEdge](https://www.pilotedge.net/pages/csl-authoring) as far as possible.

`CSL2XSB` replaces these dataRefs with the ones LiveTraffic now supports so that rotors do rotate etc. The example above will be replaced with `libxplanemp/engines/engine_rotation_angle_deg`. For a complete list of replacement dataRefs see the very beginning of the script in the map called `_DR`.
