gen_py git
check "git without args" "python3 git.py |grep -q 'the following git repos are available'"
check "git with bad arg" "python3 git.py mxww |grep -q 'no such repo'"
check "git with good arg" "python3 git.py mxw |grep -q 'git clone.*mxw'"
check "git with commit arg" "python3 git.py mxw HEAD |grep -q 'http://git.frugalware.org/gitweb/gitweb.cgi?p=mxw.git;a=commitdiff;h=HEAD'"
check "git with info arg" "python3 git.py info mxw|grep -q \"desc: '.*', owner: '.*'\""
