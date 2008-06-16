gen_py wtf
check "resolve wtf" "[ \"\$(python wtf.py wtf)\" == \"privmsg: source: WTF: {what,where,who,why} the fuck\" ]"
check "don't resolve wtff" "[ \"\$(python wtf.py wtff)\" == \"privmsg: source: wtff: nothing appropriate\" ]"
