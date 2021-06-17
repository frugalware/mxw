gen_py anongit
check "anongit without args" "python3 anongit.py |grep -q \"'anongit' requires a parameter. use the 'git' command to list available repos\""
check "anongit with bad arg" "python3 anongit.py mxww |grep -q 'no such repo'"
check "anongit with good arg" "python3 anongit.py mxw |grep -q 'git clone https://.*mxw'"
