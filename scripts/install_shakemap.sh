#!/usr/bin/env bash

# Function definition
set_profile() {
    unamestr=`uname`
    if [ "$unamestr" == 'Linux' ]; then
        prof=~/.bashrc
        matplotlibdir=~/.config/matplotlib
    elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
        prof=~/.bash_profile
        matplotlibdir=~/.matplotlib
    else
        echo "Unsupported environment. Exiting."
        exit
    fi

    # execute the user's profile
    echo "Sourcing the profile file ${prof}"
    source $prof
}

activate_base() {
    # Start in conda base environment
    # The documentation for this command says:
    # "writes the shell code to register the initialization code for the conda shell code."
    # The ShakeMap developers will buy an ice cream for anyone who can explain the previous sentence.
    # whatever it does, it is crucially important for being able to activate a conda environment
    # inside a shell script.
    eval "$(conda shell.bash hook)"                                                
    conda activate base
    if [ $? -ne 0 ]; then
        echo "Failed to activate conda base environment. Exiting."
        exit 1
    fi
}

get_yaml() {
    # Do os-specific conda dependencies
    if [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
        # This is motivated by the mysterios pyproj/rasterio error and incorrect results
        # that only happen on ARM macs. 
        # https://github.com/conda-forge/pyproj-feedstock/issues/156
        input_yaml_file=osx_environment.yml
    else
        input_yaml_file=linux_environment.yml
    fi
    echo $input_yaml_file
}

setup_matplotdir() {
    # create a matplotlibrc file with the non-interactive backend "Agg" in it.
    if [ ! -d "$matplotlibdir" ]; then
        mkdir -p $matplotlibdir
        # if mkdir fails, bow out gracefully
        if [ $? -ne 0 ];then
            echo "Failed to create matplotlib configuration file. Exiting."
            exit 1
        fi
    fi

    matplotlibrc=$matplotlibdir/matplotlibrc
    if [ ! -e "$matplotlibrc" ]; then
        echo "backend : Agg" > "$matplotlibrc"
        echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
    elif grep -Fxq "backend : Agg" $matplotlibrc ; then
        :
    elif ! grep -Fxq "backend" $matplotlibrc ; then
        echo "backend : Agg" >> $matplotlibrc
        echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
    else
        if [[ "$unamestr" == "Darwin" ]]; then
            sed -i '' 's/backend.*/backend : Agg/' $matplotlibrc
        else
            sed -i 's/backend.*/backend : Agg/' $matplotlibrc
        fi
        echo "NOTE: $matplotlibrc has been changed to set 'backend : Agg'"
    fi
}

install_conda() {
    # Is conda installed?
    conda --version >> /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "No conda detected, installing from miniforge..."
        command -v curl >/dev/null 2>&1 || { echo >&2 "Script requires curl but it's not installed. Aborting."; exit 1; }
        miniforge_url="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
        curl -L $miniforge_url -o miniforge.sh &>/dev/null
        # if curl fails, bow out gracefully
        if [ $? -ne 0 ];then
            echo "Failed to download miniforge installer shell script. Exiting."
            exit 1
        fi
        echo "Install directory: $HOME/miniforge"
        bash miniforge.sh -f -b -p $HOME/miniforge &>/dev/null
        # if miniforge.sh fails, bow out gracefully
        if [ $? -ne 0 ];then
            echo "Failed to run miniforge installer shell script. Exiting."
            exit 1
        fi
        
        $HOME/miniforge/bin/conda init bash &>/dev/null
        # Source the appropriate profile for the OS (set by set_profile function)
        source $prof

        # remove the shell script
        rm miniforge.sh
    fi
}

update_conda() {
    # Update the conda tool
    CVNUM=`conda -V | cut -f2 -d' '`
    LATEST=`conda search conda | tail -1 | tr -s ' ' | cut -f2 -d" "`
    # echo "${CVNUM}"
    # echo "${LATEST}"
    if [ ${LATEST} != ${CVNUM} ]; then
        echo "Updating conda tool..."
        CVERSION=`conda -V`
        echo "Current conda version: ${CVERSION}"
        conda update -n base conda -y
        CVERSION=`conda -V`
        echo "New conda version: ${CVERSION}"
        echo "Done updating conda tool..."
    else
        echo "conda ${CVNUM} already matches latest version ${LATEST}. No update required."
    fi

}

install_conda_lock() {
    # Use a dedicated environment for conda-lock to avoid polluting base
    CONDA_LOCK_ENV="conda-lock"
    
    if ! conda env list | grep -q "^${CONDA_LOCK_ENV} "; then
        echo "Creating dedicated environment for conda-lock..."
        conda create -n ${CONDA_LOCK_ENV} -c conda-forge conda-lock -y >> "${logfile}" 2>&1
        if [ $? -ne 0 ]; then
            echo "Failed to create conda-lock environment. Exiting."
            exit 1
        fi
    else
        echo "conda-lock environment already exists."
        # Verify conda-lock is actually installed there
        if ! conda list -n ${CONDA_LOCK_ENV} | grep -q '^conda-lock '; then
            echo "Repairing conda-lock environment..."
            conda install -n ${CONDA_LOCK_ENV} -c conda-forge conda-lock -y >> "${logfile}" 2>&1
            if [ $? -ne 0 ]; then
                echo "Failed to repair conda-lock environment. Exiting."
                exit 1
            fi
        fi
    fi
    
    # Force conda-lock to use conda instead of mamba (conda 23.10+ has libmamba built-in)
    export CONDA_LOCK_NO_MAMBA=1
}

get_python_version() {
    directory=$1
    python_version=`grep "requires-python" ${directory}/pyproject.toml | cut -f3 -d"=" | cut -f1 -d","`
    echo $python_version
}

# Set some default arguments
# Default is to use conda to install since mamba fails on some systems
install_pgm=conda
developer=false
VENV=shakemap
NVERSIONS=5
shakemap_repo="https://code.usgs.gov/ghsc/esi/shakemap.git"

directory=""
version=""

while getopts ":v:d:e:lh" opt; do
  case $opt in
    v)
      version=$OPTARG
      # echo "Version: $version"
      ;;
    d)
      directory=$OPTARG
      # echo "Directory: $directory"
      ;;
    e)
      VENV=$OPTARG
      ;;
    l)
      echo "Listing most recent tags:"
      git ls-remote --tags ${shakemap_repo} | grep "v[0-9].[0-9]" | grep -v "\^" | grep -v "beta" | cut -f3 -d"/" | tail -5
      exit 0
      ;;
    h)
      echo "Install a specific ShakeMap version from a tag (i.e., v4.4.6)"
      echo ""
      echo "This script will: "
      echo " - clone the specified ShakeMap tag to a temporary directory"
      echo " - install the python 'build' module"
      echo " - build a Python 'wheel' file"
      echo " - Use pip to install ShakeMap from the 'wheel'"
      echo " - Clean up all temporary files/directories"
      echo ""
      echo "A log file will be written in the directory specified (defaults to user's home)"
      echo "This log file will be named shakemap_install_<version>_<YYYYMMDDHHMMSS>.log"
      echo ""
      echo ""
      usage_string=$(cat <<EOF
Usage: $0
\t[-v Specify shakemap_version (i.e., v4.4.6)]
\t[-d directory where log file will be written (defaults to current directory)]
\t[-l list recent tags and exit]
\t[-e Set conda environment (defaults to "${VENV}")]
EOF
)
      echo -e "${usage_string}"
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

if [[ -z $version ]]; then
    echo "No version input. Exiting"
    exit 1
fi

if [[ -z $directory ]]; then
    directory=$PWD
fi

tnow=$(date +"%Y%m%d%H%M%S")
logfile="${directory}/shakemap_install_${version}_${tnow}.log"
echo "Detailed output will be written to a log file:"
echo "${logfile}"

# source the appropriate bash source file
set_profile

# Ensure that git is installed
git_exec=$(which git)
if [[ $? -ne 0 ]]; then
    echo "The 'git' command does not seem to be installed. Install this program and try again."
    exit 1
fi

# Create a temporary directory and store its path in a variable
# The '|| exit 1' ensures the script stops if mktemp fails
TEMPD=$(mktemp -d) || exit 1
# TEMPD=/home/mhearne/tmp/test_bash

# Make sure the temp directory gets removed on script exit (EXIT, HUP, INT, TERM signals)
trap 'rm -rf "$TEMPD"' EXIT HUP INT TERM

# --- Your script logic goes here ---
echo "Doing work in $TEMPD (this will be deleted when script finishes or errors out)..."
cd $TEMPD

echo "Using git to clone the ShakeMap tag ${version}..."
git clone -b ${version} --depth 1 ${shakemap_repo} shakemap >> ${logfile} 2>&1

if [[ $? -ne 0 ]]; then
    echo "The 'git clone' command failed. Check the input ShakeMap version against known tags."
    exit 1
fi

# install conda if it is not found
echo "Checking to see if conda is installed on the system, installing from miniforge if not..."
install_conda

# activate the base environment
echo "Activating base virtual environment..."
activate_base

# update conda tool
update_conda

# Remove standalone mamba if present (conda 23.10+ has libmamba built-in)
echo "Checking for standalone mamba installation..."
if conda list -n base | grep -q '^mamba '; then
    echo "Removing standalone mamba (conda 23.10+ already includes libmamba solver)..."
    conda remove -n base mamba -y >> ${logfile} 2>&1
fi

# Install conda-lock if needed
install_conda_lock

# Remove existing shakemap environment if it exists
echo "Remove existing ${VENV} environment if it exists..."
${install_pgm} remove -y -n $VENV --all >> ${logfile} 2>&1
${install_pgm} clean -y --tarballs >> ${logfile} 2>&1

# Set up a non-interactive matplotlib backend 
echo "Configuring the plotting library to only render figures to file output..."
setup_matplotdir

# Check if conda-lock.yml exists in the cloned repository
lockfile="${TEMPD}/shakemap/conda-lock.yml"

if [ -f "$lockfile" ]; then
    echo "Lock file found: ${lockfile}"
    echo "Installing environment from lock file..."
    CONDA_LOCK_NO_MAMBA=1 conda run -n conda-lock conda-lock install --name $VENV ${lockfile} >> ${logfile} 2>&1
    
    if [ $? -ne 0 ]; then
        echo "Failed to create environment from lock file."
        
        if [ "$unamestr" == 'Linux' ] && grep -q "manylinux.*is not a supported wheel" ${logfile}; then
            echo ""
            echo "Minimum glibc version required: 2.28"
            echo ""
            echo "Falling back to YAML environment file..."
            echo ""
            
            echo "Cleaning up partial environment..."
            CONDA_ROOT=$(conda info --base)
            if [ -d "${CONDA_ROOT}/envs/${VENV}" ]; then
                rm -rf "${CONDA_ROOT}/envs/${VENV}"
            fi
            
            input_yaml_file="${TEMPD}/shakemap/$(get_yaml)"
            
            if [ -f "$input_yaml_file" ]; then
                echo "Installing from ${input_yaml_file}..."
                ${install_pgm} env create -f ${input_yaml_file} -n $VENV >> ${logfile} 2>&1
                
                if [ $? -ne 0 ]; then
                    echo "Failed to create conda environment from YAML. Check ${logfile} for details."
                    exit 1
                fi
            else
                echo "No fallback YAML file found. Exiting."
                exit 1
            fi
        else
            echo "Check ${logfile} for details."
            exit 1
        fi
    fi
else
    echo "Lock file not found, falling back to YAML method..."
    # Get the conda input yaml file appropriate for user's platform
    input_yaml_file="${TEMPD}/shakemap/$(get_yaml)"
    
    if [ -f "$input_yaml_file" ]; then
        echo "YAML file to use for installing conda dependencies: ${input_yaml_file}"
    else
        echo "File $input_yaml_file does not exist or is not a regular file."
        exit 1
    fi
    
    # Install the virtual environment
    echo "Creating new environment from environment file: ${input_yaml_file}..."
    ${install_pgm} env create -f ${input_yaml_file} -n $VENV >> ${logfile} 2>&1
    
    if [ $? -ne 0 ]; then
        echo "Failed to create conda environment. Resolve any conflicts, then try again."
        exit 1
    fi
fi

# Activate the new environment
echo "Activating the $VENV virtual environment..."
conda activate $VENV
if [ $? -ne 0 ]; then
    echo "Failed to activate ${VENV} environment. Exiting."
    exit 1
fi

cd $TEMPD/shakemap

echo "Installing necessary Python build tool..."
pip install build >> ${logfile} 2>&1

echo "Compiling shakemap into a 'wheel' file for easier installation..."
python -m build >> ${logfile} 2>&1

wheelfile=`find . -name '*.whl'`

echo "Using 'pip' to install shakemap from wheel file ${wheelfile}..."
pip install $wheelfile | tee -a ${logfile}

echo "Installation complete."
echo ""
echo "Activate the ${VENV} conda environment:"
echo ""
echo "If this is your first time using conda:"
echo "  ~/miniforge/bin/conda init bash"
echo "  # Then run: source ~/.bashrc (Linux) or source ~/.bash_profile (macOS)"
echo ""
echo "conda activate ${VENV}"
echo "sm_profile -c <desired_profile_name> (follow the prompts) OR"
echo "sm_profile -c <desired_profile_name> -a (installs everything automatically)"
echo "Check that the installed version of shakemap matches the input:"
echo "'shake -v' - this should return 'ShakeMap version ${version})'"

# Clean up package cache now that installation is complete
echo "Cleaning conda package cache..."
conda clean -y --tarballs >> ${logfile} 2>&1

# Remove temporary conda-lock environment
echo "Removing temporary conda-lock environment..."
conda env remove -n conda-lock -y >> ${logfile} 2>&1

echo ""
echo "Installation and cleanup complete."
# When the script ends (reaches this point or exits due to an error), 
# the trap will execute and remove $TEMPD and all its contents recursively.