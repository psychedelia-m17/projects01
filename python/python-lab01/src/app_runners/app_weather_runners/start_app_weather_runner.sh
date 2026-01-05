#!/bin/bash

python_program_file="app_weather_runner.py"
python_program_dir="$(dirname ${0})"
python_program_path="${python_program_dir}/${python_program_file}"

python_path="${0%src/*}src"
export PYTHONPATH="${PYTHONPATH}:${python_path}"

echo "Running: ${python_program_path}"
echo "PYTHONPATH: ${PYTHONPATH}"
python3 ${python_program_path}
