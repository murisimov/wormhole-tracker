if [ -z "$(ls . | grep 'deploy.sh')" -o -z "$(ls . | grep 'setup.py')" ]; then
    echo; echo 'Please launch deploy script right from application root directory'; echo
    exit 1
fi

appname="wormhole-tracker"
envdir="${HOME}/.envs/${appname}"
daemon="/etc/init.d/${appname}"

${daemon} stop &> /dev/null
rm -f ${daemon} &> /dev/null

# Add user htpass, so Apache can launch our virtualhost
if id -u ${appname} > /dev/null; then
    echo; echo "${appname} user exists"; echo
else
    if useradd ${appname} -m -b /home -s /bin/bash -U; then
        echo; echo "${appname} user created"; echo
    else
        echo; echo "Failed to create ${appname} user"; echo
        exit 1
    fi
fi

# Install virtualenv
if pip install virtualenv; then
    # Create vitrualenv for our app
    mkdir -p ~/.envs
    if virtualenv ${envdir}; then
        # Install dependencies under virtualenv
        if ${envdir}/bin/python setup.py install --record files.txt; then
            echo; echo "Application installed"; echo
        else
            echo; echo "Failed to install application"; echo
            exit 1
        fi
    else
        echo; echo "Failed to create virtualenv"; echo
        exit 1
    fi
else
    echo; echo "Failed to install virtualenv"; echo
    exit 1
fi


if cp ${appname}/daemon/${appname} /etc/init.d/; then
    echo; echo "Daemon script installed"; echo
else
    echo; echo "Failed to copy daemon script to /etc/init.d/"; echo
    exit 1
fi

${daemon} start
