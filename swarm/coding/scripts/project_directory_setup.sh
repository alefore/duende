#!/usr/bin/bash

set -e

git clone ../../master repository

mkdir research data

cat >plan.md <<EOF
## Goal: $1

$2

## Task: Plan execution of the project

Do a superficial investigation of the source code repository
and schedule additional research, implementation and/or planning tasks.
The set of tasks scheduled must result in completion of the project.
EOF
