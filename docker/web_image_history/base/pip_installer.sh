#!/bin/bash

req_files=`ls ./requirements/*.txt | sort -V`
for req in $req_files
do
  echo "Installing $req"
   pip install -r $req
done