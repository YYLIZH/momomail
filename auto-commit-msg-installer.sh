#!/bin/bash

# NOTE: This script is meant to be run from the root of your git repository
# curl -s https://raw.githubusercontent.com/leonavevor/auto-gen-git-commit-msg/main/auto-commit-msg-installer.sh | bash

PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Clone the auto-gen-git-commit-msg repo
git clone https://github.com/leonavevor/auto-gen-git-commit-msg.git ${PROJECT_ROOT}/.tmp/auto-gen-git-commit-msg || true


# create the .git/hook-utils directory
mkdir -p ${PROJECT_ROOT}/.git/hook-utils


# # create __init__.py file in the .git/hook-utils directory
touch ${PROJECT_ROOT}/.git/hook-utils/__init__.py


# Install the git hooks
make -C ${PROJECT_ROOT}/.tmp/auto-gen-git-commit-msg SHELL='sh -x' install-git-commit-msg-hook
 
# Clean up the temp Makefile
# comment out the following line if you want to keep the .tmp folder
# ... to be able to run the auto-gen-git-commit-msg manually
# like this: 'python .tmp/auto-gen-git-commit-msg/gen_git_commit_msg_openai.py' 
rm -rf ${PROJECT_ROOT}/.tmp || true

# reload zsh and bash
exec zsh -l
exec bash -l