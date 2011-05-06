#!/bin/sh

d=`(cd apps ; for i in *; do  if (test -d "$i") then { echo $i; } fi; done)`
for i in $d; do 
    echo $i;
    ./manage.py schemamigration $i --auto
done
