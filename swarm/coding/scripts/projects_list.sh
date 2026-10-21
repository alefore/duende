#!/usr/bin/bash
dir="swarm/products/$1/projects"
if [ -z "$(find "$dir" -maxdepth 0 -empty)" ]; then
  echo "<ongoing_projects product='$1'>"
  ls "$dir"
  echo "</ongoing_projects>"
else
  echo "$1: No ongoing projects."
fi
