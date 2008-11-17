gen_py wtf
check "resolve wtf" "[ \"\$(python wtf.py wtf)\" == \"privmsg: source: WTF: {what,where,who,why} the fuck\" ]"
check "don't resolve wtff" "[ \"\$(python wtf.py wtff)\" == \"privmsg: your search did not match any documents\" ]"
