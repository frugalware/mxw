gen_py help
check "help without args" "python3 help.py |grep -q ': [0-9]\+ available commands: '"
check "help with invalid arg" "python3 help.py helpp |grep -q ': no such command\$'"
