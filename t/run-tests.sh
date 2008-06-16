#!/bin/sh

passed=0
failed=0

check()
{
	echo -n "test $(($passed+$failed+1)): $1..."
	eval $2
	if [ $? == 0 ]; then
		echo " passed."
		passed=$(($passed+1))
	else
		echo " failed."
		failed=$(($failed+1))
	fi
}

check "good tv channel -> notice" "python tv.py 'Discovery Travel'|grep -q ^notice"
check "bad tv channel -> privmsg" "python tv.py 'Discovery Travell'|grep -q ^privmsg"
check "resolve wtf" "[ \"\$(python wtf.py wtf)\" == \"privmsg: source: WTF: {what,where,who,why} the fuck\" ]"
check "don't resolve wtff" "[ \"\$(python wtf.py wtff)\" == \"privmsg: source: wtff: nothing appropriate\" ]"
check "choose foo or bar" "python choose.py foo bar |egrep -q '^privmsg: source: (foo|bar)\$'"

echo "passed: $passed, failed $failed"

if [ $failed -gt 0 ]; then
	exit 1
else
	exit 0
fi
