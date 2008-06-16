gen_py choose
check "choose foo or bar" "python choose.py foo bar |egrep -q '^privmsg: source: (foo|bar)\$'"
