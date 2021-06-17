gen_py choose
check "choose foo or bar" "python3 choose.py foo bar |egrep -q '^privmsg: source: (foo|bar)\$'"
