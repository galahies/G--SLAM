#!/usr/bin/env bash

wget https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip
unzip Replica.zip
rm Replica.zip

cd Replica || exit 1
wget https://cvg-data.inf.ethz.ch/nice-slam/data/replica_mesh.zip
unzip replica_mesh.zip
mv replica_mesh gt_mesh_culled
