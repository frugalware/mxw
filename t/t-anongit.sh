gen_py anongit
check "anongit without args" "python anongit.py |grep -q \"'anongit' requires a parameter. use the 'git' command to list available repos\""
check "anongit with bad arg" "python anongit.py mxww |grep -q 'no such repo'"
check "anongit with good arg" "python anongit.py mxw |grep -q 'git clone http://.*mxw'"
