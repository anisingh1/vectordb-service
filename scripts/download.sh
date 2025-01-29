#!/bin/bash

modeldir=$1
token=$2
modelfile="$modeldir".tar.gz
parentdir="$(dirname "$modeldir")"
tgtfilename="$(basename "$modeldir").tar.gz"

if [ -d $modeldir ]
then
    echo "Model files already exists."
    if [ -f $modelfile ]
    then
        rm $modelfile
    fi
else
    if [ -f $modelfile ]
    then
        echo "Skipping download..."
        cd $parentdir
        tar -xzvf $tgtfilename
        rm $tgtfilename
    else
        echo "Downloading model..."
        mkdir -p $parentdir
        cd $parentdir
        artifactoryPath="https://artifactory-uw2.adobeitc.com/artifactory/generic-g11n-content-release/semanticmatch/${tgtfilename}"
        curl -H "X-JFrog-Art-Api:$token" -L -o $tgtfilename --retry 3 $artifactoryPath
        tar -xzvf $tgtfilename
        rm $tgtfilename
    fi
fi