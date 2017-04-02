#!/bin/sh
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

# This script does the following:
# - Checks if it's running from the correct dir
# - Checks if there is a valid python version available
# - Removes old daemon file if it exists
# - Adds user which will run the daemon
# - Installs virtualenv python package
# - Sets up the venv for the application
# - Installs application itself
# - Installs application daemon
# - Starts application daemon.


app_name="wormhole-tracker"
app_dir="wormhole_tracker"

envs_dir="${HOME}/.envs"  # Edit this if you already have your own python environments elsewhere

app_env="${envs_dir}/${app_name}"
daemon="/etc/init.d/${app_name}-daemon"
py_version="3.6"

print () {
    echo; echo $1; echo
}

# Check if script is running from the correct place
if [ -z "$(ls . | grep 'deploy.sh')" -o -z "$(ls . | grep 'setup.py')" ]; then
    print 'Please launch deploy script right from application root directory'
    exit 1
fi

# Check if correct python version is installed
if [ -z "$(which python${py_version} 2>/dev/null | grep -E "(/\w+)+/python${py_version}")" ]; then
    print 'Seems like python3.6 is not installed. Please install python3.6 first.'
    exit 1
fi

${daemon} stop &> /dev/null
rm -f ${daemon} &> /dev/null

print "Adding user '${app_name}'..."
if id -u ${app_name} > /dev/null; then
    print "User '${app_name}' already exists, skipping."
else
    if useradd ${app_name} -m -b /home -s /bin/bash -U; then
        print "User '${app_name}' have been created."
    else
        print "Failed to create user '${app_name}', aborting."
        exit 1
    fi
fi

print "Installing virtualenv..."
if pip install virtualenv; then
    # Create vitrualenv for the app
    mkdir -p ${envs_dir}

    if [ -d "${app_env}" ]; then
        print "Cleaning old virtualenv..."
        rm -rf ${app_env}
    fi

    print "Success. Creating virtualenv for ${app_name}..."
    if python${py_version} -m venv ${app_env}; then
        print "Success. Installing ${app_name} application..."
        # Install application and its dependencies under virtualenv
        if ${app_env}/bin/python setup.py install --record files.txt >install.log; then
            print "Application installed."
        else
            print "Failed to install application, aborting."
            exit 1
        fi
    else
        print "Failed to create virtualenv, aborting."
        exit 1
    fi
else
    print "Failed to install virtualenv, aborting."
    exit 1
fi

print "Installing ${app_name} daemon..."
if cp ${app_dir}/daemon/${app_name}-daemon /etc/init.d/; then
    print "Daemon script installed."
else
    print "Failed to copy daemon script to the /etc/init.d/"
    exit 1
fi

${daemon} start
