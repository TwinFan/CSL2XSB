#!/usr/bin/python3

"""
Converts CSL packages to the original XSB format for use in LiveTraffic (and probably XSquawkBox)
For usage info call
    python3 CSL2XSB.py -h


MIT License

Copyright (c) 2019 B.Hoppe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from pathlib import Path, PurePath
import argparse                     # handling command line arguments

_currAircraft = ''                  # name of currently processed aircraft
_warnings = 0                       # number of warnings

def UpdateOBJ8File(in_p:Path, out_p:Path, textureLivery:str = None, textureLit:str = None):
    """Updates the OBJ8 file: TEXTURE and dataRefsself."""

    global _warnings

    if args.verbose:
        print ('   -- Writing   ', out_p.name, '  (from ' + in_p.name + '):')

    assert(in_p.is_file())
    in_f = None
    out_f = None
    try:
        # open in/out files
        in_f = in_p.open(mode='r',encoding='ascii',errors='replace')
        out_f = out_p.open(mode='w',encoding='ascii',errors='replace')

        # read all lines, copy most of them 1:1 to the output
        for line in in_f:
            # remove the newline char from the end
            line = line.rstrip('\n\r')
            origLine = line
            word = line.split()
            numWords = len(word)

            if numWords >= 1:
                # replace texture
                if textureLivery is not None and word[0] == 'TEXTURE':
                    line = 'TEXTURE ' + textureLivery

                # replace LIT texture
                if textureLit is not None and word[0] == 'TEXTURE_LIT':
                    line = 'TEXTURE_LIT ' + textureLit

            # write to output
            if args.verbose and line != origLine:
                print ('      Written:   ' + line + '  (instead of ' + origLine + ')')
            out_f.write(line+'\n')

    except IOError as e:
        parser.error('UpdateOBJ8File failed:\n' + e.filename + ':\n'+ e.strerror +'\n')

    finally:
        # cleanup
        if in_f is not None:
            in_f.close()
        if out_f is not None:
            out_f.close()


def HandleXsbObj8Solid(path: Path, line: str) -> str:
    """Deals with the OBJ8 SOLID line.

    Example: OBJ8 SOLID YES MD80/MD80.obj AZA.png MD80_LIT.png
    Means:
    - Identify that it has additional texture info and, hence, requires treatment
    - Have the original OBJ8 file (MD80.obj) treated and MD80_AZA.obj created
    Returns the line for the new xsb_aircraft file, which would be:
        BJ8 SOLID YES MD80/MD80_AZA.obj
    or None if no change occurred.
    """

    global _warnings

    # --- split the line into its parameters (after removing any line ending) ---
    word = line.split()
    numWords = len(word)
    if numWords < 4:                  # too few parameters!
        print ('   ERROR - Too few parameters, skipped: ' + line)
        return None

    # the object file's name (replace colons [X-CSL comes this way...?] with forward slash)
    object_in_p = PurePath(word[3].replace(':','/'))
    package_name = object_in_p.parts[0]
    # the first part of the Object path just refers to the arbitrary CSL EXPORT_NAME,
    # strip it to get the file name of the current OBJ8 file:
    obj8_in_file_p = path / object_in_p.relative_to(package_name)

    # --- No additional parameters for livery textures?
    #     Example: OBJ8 SOLID YES MD80/MD80.obj
    if numWords == 4:
        if args.noupdate:                   # and no update of OBJ8?
            if args.verbose:
                print ('   No change to: ' + line)
            return None                     # return with no change

        # so we rename the existing file to ...orig
        obj8_out_file_p = obj8_in_file_p
        obj8_in_file_p = obj8_in_file_p.with_name(obj8_in_file_p.name + '.orig')
        if not obj8_in_file_p.is_file():    # ...if it isn't there already
            if not obj8_out_file_p.is_file():
                print ('   ERROR - ' + _currAircraft + ': Cannot access OBJ8 file, skipped: ' + str(obj8_out_file_p))
                return None
            obj8_out_file_p.rename(obj8_in_file_p)
            if args.verbose:
                print ('   Renamed', obj8_out_file_p,'-->',obj8_in_file_p.name)

        # Update the OBJ8 file
        UpdateOBJ8File(obj8_in_file_p, obj8_out_file_p)

        # but no change to the xsb_aircraft line
        return line

    # --- Normal case: additional texture parameters on the line,
    #                  so we need to create a new OBJ8 file
    else:
        # original OBJ8 file must be accessible
        if not obj8_in_file_p.is_file():
            print ('   ERROR - ' + _currAircraft + ': Cannot access OBJ8 file, skipped: ' + str(obj8_in_file_p))
            return None

        # livery texture and Lit texture
        textureLivery_p = path / word[4]
        if not textureLivery_p.is_file():
            if textureLivery_p.with_suffix('.png').is_file():           # X-CSL sometimes has wrong suffix in xsb_aircraft.txt, i.e. couldn't have worked, fix it, too.
                print ('   WARNING - {}: Could not find texture file {}, but found and used {}'.format(_currAircraft, textureLivery_p, textureLivery_p.with_suffix('.png').name))
                textureLivery_p = textureLivery_p.with_suffix('.png')
            if textureLivery_p.with_suffix('.dds').is_file():
                print ('   WARNING - {}: Could not find texture file {}, but found and used {}'.format(_currAircraft, textureLivery_p, textureLivery_p.with_suffix('.dds').name))
                textureLivery_p = textureLivery_p.with_suffix('.dds')
            else:
                print ('   WARNING - '+_currAircraft+': Cannot find texture file, continue anyway: ', textureLivery_p)
                _warnings += 1

        # also Lit texture defined?
        textureLit_p = None
        if numWords >= 6:
            textureLit_p = path / word[5]
            if not textureLit_p.is_file():
                if textureLit_p.with_suffix('.png').is_file():
                    print ('   WARNING - {}: Could not find lit texture file {}, but found and used {}'.format(_currAircraft, textureLit_p, textureLit_p.with_suffix('.png').name))
                    textureLit_p = textureLit_p.with_suffix('.png')
                elif textureLit_p.with_suffix('.dds').is_file():
                    print ('   WARNING - {}: Could not find lit texture file {}, but found and used {}'.format(_currAircraft, textureLit_p, textureLit_p.with_suffix('.dds').name))
                    textureLit_p = textureLit_p.with_suffix('.dds')
                else:
                    print ('   WARNING - '+_currAircraft+': Cannot find lit texture file, continue anyway: ', textureLit_p)
                    _warnings += 1

        # compile the new object file's name, combined from original and livery files:
        obj8_out_file_p = obj8_in_file_p.with_name(obj8_in_file_p.stem + '_' + textureLivery_p.stem + obj8_in_file_p.suffix)
        object_out_p = PurePath(package_name) / obj8_out_file_p.relative_to(path)

        # Update the OBJ8 file
        UpdateOBJ8File(obj8_in_file_p, obj8_out_file_p,         \
                       str(textureLivery_p.relative_to(path)),                    \
                       str(textureLit_p.relative_to(path)) if textureLit_p is not None else None)

        # --- return the new line for the xsb_aircraft file ---
        newLn = word[0] + ' ' + word[1] + ' ' + word[2] + ' ' + str(object_out_p)
        return newLn


def ConvFolder(path: Path) -> int:
    """Converts the CSL package in the given path, recursively for each folder.

    Returns the number of written OBJ8 objects."""

    numObj = 0;
    global _currAircraft
    _currAircraft = '?'

    # --- Save the current version of xsb_aircraft as .orig, which we then read from ---
    assert (path.is_dir())
    xsb_aircraft_p = path / 'xsb_aircraft.txt'
    xsb_aircraft_orig_p = path / 'xsb_aircraft.txt.orig'

    # First check of any of the two exists, otherwise we consider this folder empty:
    if (not xsb_aircraft_p.is_file() and not xsb_aircraft_orig_p.is_file()):
        if args.verbose:
            print ('===(skipped)', path)

        # --- Recursion: We check for containing folders and try again there!
        if not args.norecursion:
            for folder in path.iterdir():
                if folder.is_dir():
                    numObj += ConvFolder(folder)

        return numObj;

    # So we will process this path
    print ('=========>  ', path)

    try:
        # If the .orig version _not_ already exists then assume current xsb_aircraft.txt _is_ the original and rename it
        # (Never change the .orig file!)
        if not xsb_aircraft_orig_p.exists():
            xsb_aircraft_p.replace(xsb_aircraft_orig_p)
            if args.verbose:
                print ('Renamed',xsb_aircraft_p,'-->',xsb_aircraft_orig_p)

        # --- Read from .orig as the original master ---
        xsb_aircraft_orig_f = xsb_aircraft_orig_p.open(mode='r',encoding='ascii',errors='replace')
        if args.verbose:
            print ('Reading from', xsb_aircraft_orig_p)

        # --- Write to a new xsb_aircraft.txt file (overwrite existing one!) ---
        xsb_aircraft_f = xsb_aircraft_p.open(mode='w',encoding='ascii',errors='replace')
        if args.verbose:
            print ('Writing to  ', xsb_aircraft_p)

        # --- We track ICAO/AIRLINE to identify the case when the xsb_aircraft
        #     file defines a LIVERY line without defining an AIRLINE line.
        #     LiveTraffic cannot (yet?) select one out of many liveries for
        #     one airline. Rather, there should be one AIRLINE entry in
        #     xsb_aircraft that defines the standard livery per airline.
        #     The other liveries are not easily accessible. LiveTraffic
        #     provides the tail number for full livery match but has no
        #     knowledge of proprietory names like "S", "S2", "S3" (as they
        #     are sometimes used in the X-CSL package for exampele).
        #
        #     Similar is true for the ICAO line: One of the entries
        #     should be the default plane if there is no matching
        #     airline so that we at least can find the right model.
        currIcaoType = ''
        currAirline = ''

        # --- Read all lines from .orig file
        # Most of them are just copied 1:1 to the output file
        for line in xsb_aircraft_orig_f:
            # remove the newline char from the end
            line = line.rstrip('\n\r')
            origLine = line
            word = line.split()
            numWords = len(word)

            if numWords >= 2:
                # This is a line with at least two words

                # OBJ8_AIRCRAFT identifies the start of another aircraft.
                # Technically, we don't need that info, but it's nice for user info
                if word[0] == 'OBJ8_AIRCRAFT':
                    # assume all else is the aircraft name
                    _currAircraft = ' '.join(word[1:])
                    if args.verbose:
                        print ('-- ' + _currAircraft)
                    # replace spaces in the aircraft name (PE does that)
                    if ' ' in _currAircraft:
                        _currAircraft = _currAircraft.replace(' ', '_')
                    # replace colons in the aircraft name (X-CSL does that, although there is no need for a path here)
                    if ':' in _currAircraft:
                        _currAircraft = _currAircraft.replace(':', '_')
                    # re-write the OBJ8_AIRCRAFT line
                    word[1] = _currAircraft
                    line = 'OBJ8_AIRCRAFT ' + _currAircraft

                # X-CSL uses non-existing ICAO code 'MD80', replace with MD81
                if word[1] == 'MD80' and        \
                   (word[0] == 'ICAO' or        \
                    word[0] == 'AIRLINE' or     \
                    word[0] == 'LIVERY'):
                    word[1] = 'MD81'
                    line = ' '.join(word)

                # -- track ICAO / AIRLINE (insert ICAO/AIRLINE line if only AIRLINE/LIVERY lines are in original)
                thisIcaoType = currIcaoType
                if word[0] == 'ICAO' or      \
                   word[0] == 'AIRLINE' or   \
                   word[0] == 'LIVERY':
                    thisIcaoType = word[1]
                # if the ICAO type changes then we declare this entry the default
                if thisIcaoType != currIcaoType:
                    currIcaoType = thisIcaoType
                    currAirline = ''
                    line = 'ICAO ' + currIcaoType
                # ICAO type didn't change...maybe airline does?
                elif (word[0] == 'AIRLINE' or    \
                      word[0] == 'LIVERY') and   \
                     numWords >= 3:
                    thisAirline = word[2]
                    # if airline changes then declare this entry the default for the airline
                    if thisAirline != currAirline:
                        currAirline = thisAirline
                        line = 'AIRLINE ' + currIcaoType + ' ' + currAirline

                # -- now decide what to do with the line

                # ignore deprecated or PE-extension commands
                if (word[0] == 'OBJ8' and word[1] == 'GLASS') or     \
                   (word[0] == 'OBJ8' and word[1] == 'LOW_LOD') or   \
                   word[0] == 'OFFSET':
                    line = None

                # OBJ8 SOLID/LIGHTS is the one line we _really_ need to work on!
                elif (word[0] == 'OBJ8' and (word[1] == 'SOLID' or word[1] == 'LIGHTS')):
                    Obj8SolidLine = HandleXsbObj8Solid(path, line)
                    if Obj8SolidLine is not None:
                        # and we did something to the OBJ8 line:
                        line = Obj8SolidLine
                        numObj += 1

            # -- write the resulting line out to the new xsb_aircraft file
            if line is not None:
                xsb_aircraft_f.write(line + '\n')
                if args.verbose and origLine != line:
                    print ('   Written:      ' + line + '  (instead of: ' + origLine + ')')
            else:
                if args.verbose:
                    print ('   Removed line: ' + origLine)

        # --- Done, cleanup
        xsb_aircraft_f.close()
        xsb_aircraft_orig_f.close()
        print ('            ', path, 'done, converted', numObj, 'OBJ8 files')
        return numObj

    except IOError as e:
        parser.error('Converting folder ' + str(path) + ' failed:\n' + e.filename + ':\n'+ e.strerror +'\n')




""" === MAIN === """
# --- Handling command line argumens ---
parser = argparse.ArgumentParser(description='Convert CSL packages to original XSB format. Tested with: X-CSL.',fromfile_prefix_chars='@')
parser.add_argument('path', help='Base path, searched recursively for CSL packages identified by existing xsb_aircraft.txt files')
parser.add_argument('--noupdate', help='Suppress update of OBJ8 files if there are no additional textures', action='store_true')
parser.add_argument('--norecursion', help='Do not search directories recursively', action='store_true')
parser.add_argument('-v', '--verbose', help='More detailed output about every change', action='store_true')

args = parser.parse_args()

# normalize the path, resolves relative paths and makes nice directory delimiters
basePath = Path(args.path)
if not basePath.exists() or not basePath.is_dir():
    parser.error('Base bath "' + str(basePath) + '" does not exist or is no directory.')

if args.verbose:
    print ('Base path:  ', basePath)

# --- Do it ---
numConverted = ConvFolder(basePath)
print ('Done. Converted ' + str(numConverted) + ' OBJ8 files in total. Produced ' + str(_warnings) + ' warning(s).')

# --- Done ---
exit(0)
