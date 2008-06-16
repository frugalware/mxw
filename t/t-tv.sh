gen_py tv
check "good tv channel -> notice" "python tv.py 'Discovery Travel'|grep -q ^notice"
check "bad tv channel -> privmsg" "python tv.py 'Discovery Travell'|grep -q ^privmsg"
