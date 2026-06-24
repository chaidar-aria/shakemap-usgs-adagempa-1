## main

    - Add product-version argument that can override version number
    - Updated shakemap-modules dependency to 1.1.18
    - Updated rupture imports to use esi-shakelib
    - Added integration test script and reference json
    - Added instructions for running integration test for new release
    - Updated sm_create so that the "-e" option sets event type to be SCENARIO by default.
    - Update shakemap-module dependency to 1.1.18 (product version argument)
    - Update sm-rupture to plot rupture and support SRCMOD, vectorized input, and rupture.json
    - Archived 2020 manual so we can start revising a new version of the docs
    - Updated user install script to default to latest tagged version
    - Archived the html of the current docs to archive/docs2020
    - Archived the source for the current docs to archive/doc_source2020
    - Renamed the directory holding the ShakeMap3.5 doc source from archive/doc_source to archive/doc_source3.5/
    - Create new doc_draft directory for developing new documentation. 

## v4.4.9 / 2025-03-10
    - Update to shakemap-modules 1.1.16
    - Regenerated conda-lock file
    - Updated release instructions for creating the conda lock file

## v4.4.8 / 2025-03-02
    - Update install scripts to be more compatible with AWS ImageBuilder install
      - No longer installing ObsPy from main repo
      - Added an option to keep the source folder so that pytests can be run

## v4.4.7 / 2025-02-25
    - Update to shakemap-modules 1.1.15
    - Moved install scripts into scripts folder. 
      - There is a user install script (conda-lock) and a development install script (same as before).
      - ObsPy will install from git master branch to avoid setuptools error
    - Add conda-lock support for pinning environmental dependencies
    - Fix broken links in docs (mostly to github).
    - Pin scipy version to >=1.16.0 and <1.17.0 to resolve Amazon Machine Image build issue.

## v4.4.6 / 2025-08-14
    - Update to shakemap-modules 1.1.11.

## v4.4.5 / 2025-08-01
    - Update to shakemap-modules 1.1.10.
    - Set to use numpy>=1.26.
    - Update receive_origins_gsm.py to only use reviewed origins.                  
    - Another small fix to the installation docs.
    - Fix the vs30 and topo docs.
    - Eric's fix to the install docs (outdated info about python versions).
    - Mike's fix to install.sh to properly initialize conda.
    - Rename conda install dir to be "miniforge" rather than "miniconda" to avoid confusion about what we are actually installing. 

## v4.4.4 / 2025-07-10
    - Refactor install.sh
    - Make OS-specific environment.yml files.

## v4.4.3 / 2025-07-10
    - Mike's changes to install to allow build in the cloud.

## v4.4.2 / 2025-02-28
    - Refactor strings for sqlite to single quote string literals.
    - Refactor to emove a bunch of linter warnings.
    - Eliminate a bunch of deprecation warnings (datetime.utcnow(), etc.)
    - Release limits on python and sqlite.

## v4.4.1 / 2025-02-20
    - Limit python to 3.12.7 and sqlite to 3.46.1 in source_environment.yml to                
deal with sqlite suddenly enforcing the restriction that double quotes                  
can't be used for string literals.

## v4.4.0c / 2024-09-06
    - Pin to shakemap-modules v1.0.23
    - Implicitly pin to esi-shakelib v1.0.14

## v4.4.0b / 2024-09-06
    - Pin to shakemap-modules v1.0.23
    - Pin to shakemap-modules v1.0.21

## v4.4.0a / 2024-08-23
    - Pin to shakemap-modules v1.0.20

## v4.4.0 / 2024-08-23
  - Pin to shakemap-modules v1.0.19

## v4.3.0 / 2024-04-23
 - Release v4.3.0: Now using FFSimmer rather than PS2FF.
 - Fix to receive_amps.
 - Refactor docs a bunch.
 - Add optional persistence of version history back into sm_create command.

## v4.2.1 / 2023-12-11
 - Fix small bug in se_stations when JSON has no station_type.
 - Add se_stations program for getting stationlist for scenarios.
 - Re-add persistence of version history back into sm_create.

## v4.2.0 / 2023-12-11
 - Add esi-utils-comcat to install.
 - Fix install bug -- package dependency on daemon should have been python-daemon.
 - Rev versions of esi-shakelib and shakemap-modules in pyproject.toml.
 - Add versioning info for shake to pass to the model module.
 - Modify source_environment.yml to have more flexible python version.
 - Fixes to install.sh; no longer use deployment.txt files.
 - Made tests work.
 - Modified to use pypi-based esi-shakelib and shakemap-modules.
 - Restructured code to move code into "src" directory.
 - Changed to pyproject.toml
 - Removed c directory and refactored to use esi-core.
 - Modified to allow RotD50 as an input component type.
 - Added CHANGELOG.md

## 4.1.6 / 2023-12-08
 - Fix transfer_email to work with encripter servers.
 - Bug fixes: Fix order of quotes in multigmpe.py that was disrupted by black
   formatter; fix HotSpot vs Volcanic issue in probs.py; add alpha-shapes to install.

## 4.1.5 / 2023-08-29
 - Upudate docs so that the HTML isn't tracked in the repo and will build with gitlab pipelines.
 - Fix vertical/horizontal orientation bug in station.py.
 - Modified to allow RotD50 as an input component type.
 - Added CHANGELOG.md
 - Improved support for "points" mode ShakeMap runs - `assemble -p` change and `makecsv` module.
 - Added optional persistence of version history in the sm_create command.

