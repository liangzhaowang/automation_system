#!/bin/bash

echo "pull 8G-1#"
ssh pnp007@pnp007 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-2#"
ssh bxtp@pnp-docker-bxtp "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-3#"
ssh ia@regression "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-4#"
ssh pnp008@pnp008 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-5#"
ssh pnp010@pnp010 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-6#"
ssh pnp005@pnp005 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull dev#"
ssh pnp006@pnp006 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"


echo "pull 2G-1#"
ssh pnp002@pnp002 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 2G-2#"
ssh pnp014@pnp014 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 2G-s-3#"
ssh pnp015@pnp015 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 8G-s-7#"
ssh pnp004@pnp004 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"


echo "pull 4G-1#"
ssh pnp011@pnp011 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 4G-2#"
ssh pnp012@pnp012 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"

echo "pull 4G-3#"
ssh pnp013@pnp013 "cd ~/shanshan/slave_server/; git pull origin master:master; git log -n 1"