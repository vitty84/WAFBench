#!/bin/bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Doing FTW-compatible-tool testing"

test_server=10.0.1.44.206:18080
result_file=result.txt

remote_machine=10.0.1.44
remote_log_dir=share/usr/local/nginx-1.11.5/logs
remote_username=root
remote_password=000000

mount_dir=ftw_logs

git_path=https://github.com/SpiderLabs/OWASP-CRS-regressions.git
repo_path=/tmp/OWASP-CRS-regressions
yaml_dir=$repo_path/tests

#get test set of ruleset yaml
if [ -e  $repo_path ]
then
    echo 'update repo'
    cd $repo_path
    git pull
else
    git clone $git_path $repo_path
fi
cd $basepath

#mount log directory
mount_dir=$mount_dir-$remote_machine
if [ ! -e $mount_dir ]
then
    echo "mkdir $mount_dir"
    mkdir $mount_dir
fi

mount_command="sudo mount -t cifs //$remote_machine/$remote_log_dir $mount_dir -o username=$remote_username,password=$remote_password"
if ! eval $mount_command 
then
    echo "remount directory"
    sudo umount $mount_dir
    eval $mount_command
fi
cd $basepath


#rtt
result_file=$basepath/$result_file
cd ../FTW-compatible-tool/
sudo ./rtt.sh -y $yaml_dir/ -l $basepath/$mount_dir/error.log -d $test_server -o $result_file
cd $basepath
