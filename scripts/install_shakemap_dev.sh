#!/usr/bin/env bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the parent directory (main repo directory)
REPO_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"


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
source $prof


# Do os-specific conda dependencies
if [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    # This is motivated by the mysterios pyproj/rasterio error and incorrect results
    # that only happen on ARM macs. 
    # https://github.com/conda-forge/pyproj-feedstock/issues/156
    input_yaml_file="${REPO_DIR}/osx_environment.yml"
else
    input_yaml_file="${REPO_DIR}/linux_environment.yml"
fi


# Set some default arguments
# Default is to use conda to install since mamba fails on some systems
install_pgm=conda
developer=false
VENV=shakemap

# Arguments
# usage() { echo "Usage: $0 [-d to install developer dependencies] [-n <environment name>]" 1>&2; exit 1; }
usage() { echo "$0 usage:" && grep " .)\ #" $0; exit 0; }

while getopts ":hdn:" options; do
    case $options in 
    d) # Install additional developer dependencies.
        developer=true
        ;;
    n) # Overwrite name of virtual environment.
        VENV="$OPTARG"
        ;;
    h | *) # Display help.
      usage
      exit 0
      ;;
    esac
done

echo "YAML file to use as input: ${input_yaml_file}"

# Name of virtual environment
echo "Environment to create: '${VENV}'"

# Where is conda installed?
CONDA_LOC=`which conda`
echo "Location of conda install: ${CONDA_LOC}"

# Are we in an environment
CURRENT_ENV=`conda info --envs | grep "*"`
echo "Current conda environment: ${CURRENT_ENV}"

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
elif [ ! grep -Fxq "backend" $matplotlibrc ]; then
    echo "backend : Agg" >> $matplotlibrc
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
else
    sed -i '' 's/backend.*/backend : Agg/' $matplotlibrc
    echo "NOTE: $matplotlibrc has been changed to set 'backend : Agg'"
fi

# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniforge..."
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
    . $HOME/.bashrc


    # remove the shell script
    rm miniforge.sh
else
    echo "conda detected, installing $VENV environment..."
fi


# Update the conda tool
CVNUM=`conda -V | cut -f2 -d' '`
LATEST=`conda search conda | tail -1 | tr -s ' ' | cut -f2 -d" "`
echo "${CVNUM}"
echo "${LATEST}"
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

# Set libmamba as solver
conda config --set solver libmamba &>/dev/null

# Start in conda base environment
echo "Activate base virtual environment"
# The documentation for this command says:
# "writes the shell code to register the initialization code for the conda shell code."
# The ShakeMap developers will buy an ice cream for anyone who can explain the previous sentence.
# whatever it does, it is crucially important for being able to activate a conda environment
# inside a shell script.
eval "$(conda shell.bash hook)"                                                
${install_pgm} activate base
if [ $? -ne 0 ]; then
    "Failed to activate conda base environment. Exiting."
    exit 1
fi

# Remove existing shakemap environment if it exists
${install_pgm} remove -y -n $VENV --all
${install_pgm} clean -y --all

# Install the virtual environment
echo "Creating new environment from environment file: ${input_yaml_file}"
${install_pgm} env create -f ${input_yaml_file} -n $VENV


# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    exit 1
fi

# Activate the new environment
echo "Activating the $VENV virtual environment"
${install_pgm} activate $VENV

# if conda activate fails, bow out gracefully
if [ $? -ne 0 ];then
    echo "Failed to activate ${VENV} conda environment. Exiting."
    exit 1
fi


if $developer; then
    echo "Installing shakemap with developer tools."
    conda install mathjax -y
    if ! pip install -e "${REPO_DIR}[dev,test,doc]" ; then
        echo "Installation of shakemap failed."
        exit 1
    fi
else
    echo "Installing shakemap."
    if ! pip install -e "${REPO_DIR}" ; then
        echo "Installation of shakemap failed."
        exit 1
    fi
fi

echo "*********"
echo "Reminder: Run 'conda activate ${VENV}' to enable the environment."
echo "*********"
