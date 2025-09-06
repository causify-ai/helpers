#!/bin/bash -xe
RES="1920x1080"
FPS=24
DIR=hires

#RES="320x180"
#FPS=1
#DIR=lowres

SUFFIX=optima
create_presentation_video.py --out_file $DIR/presentation_$SUFFIX.mp4 --plan plan_$SUFFIX.txt --resolution $RES --fps $FPS -v DEBUG
SUFFIX=frontier
create_presentation_video.py --out_file $DIR/presentation_$SUFFIX.mp4 --plan plan_$SUFFIX.txt --resolution $RES --fps $FPS -v DEBUG
SUFFIX=panorama
create_presentation_video.py --out_file $DIR/presentation_$SUFFIX.mp4 --plan plan_$SUFFIX.txt --resolution $RES --fps $FPS -v DEBUG
