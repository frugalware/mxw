gen_py help
check "help without args" "python help.py |grep -q ': [0-9]\+ available commands: '"
check "help with invalid arg" "python help.py helpp |grep -q ': no such command\$'"
