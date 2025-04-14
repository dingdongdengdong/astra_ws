#!/bin/bash
echo "Running init_container.sh, use this script to install libraries etc."

# Define the path to be added
BIN_PATH="/home/$USER/.local/bin"

# Check if the path is already in $PATH
if [[ ":$PATH:" != *":$BIN_PATH:"* ]]; then
    # If not, append it to .bashrc
    echo "export PATH=\$PATH:$BIN_PATH" >> ~/.bashrc
fi

source ~/.bashrc


pip install -e .
