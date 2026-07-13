#!/data/data/com.termux/files/usr/bin/bash
rm -f ~/.voice_rec.m4a
termux-microphone-record -f ~/.voice_rec.m4a -l ${1:-5} -e aac
