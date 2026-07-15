#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/../../../"

# Open Terminal app and run start.sh in the foreground to show wave logo and logs
osascript -e 'tell application "Terminal" to do script "cd '"'"$PWD"'"' && ./start.sh"'
