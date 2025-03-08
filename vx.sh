#!/bin/bash

# Check if an argument was provided
if [ -z "$1" ]; then
    echo "Error: Please provide a Python script name as an argument"
    echo "Usage: $0 script_name"
    echo "Example: $0 hello"
    exit 1
fi

# Check if the Python script exists
if [ ! -f "script/$1.py" ]; then
    echo "Error: Python script '$1.py' not found"
    exit 1
fi

# Execute the Python script
python "script/$1.py"

# Check if Python execution was successful
if [ $? -ne 0 ]; then
    echo "Error: Python script execution failed"
    exit 1
fi

exit 0