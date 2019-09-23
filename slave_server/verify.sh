#!/bin/bash

commit=`cd ~/shanshan/slave_server; git ls-remote --heads origin | grep -v master | head -n 1`
branch=${commit##*/}
if [[ "$branch" != "" ]]
then
    echo "net commit: "$branch
    git pull origin ${commit##*/}:master
    git log -n 2
else
    echo "can't get the new commit!"
fi
