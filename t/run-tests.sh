#!/bin/sh

passed=0
failed=0
junk=""

gen_py ()
{
	sed "s/@FUNCTION@/$1/g" template.py >$1.py
	junk="$junk $1.py"
}

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

gen_py tv
check "good tv channel -> notice" "python tv.py 'Discovery Travel'|grep -q ^notice"
check "bad tv channel -> privmsg" "python tv.py 'Discovery Travell'|grep -q ^privmsg"
gen_py wtf
check "resolve wtf" "[ \"\$(python wtf.py wtf)\" == \"privmsg: source: WTF: {what,where,who,why} the fuck\" ]"
check "don't resolve wtff" "[ \"\$(python wtf.py wtff)\" == \"privmsg: source: wtff: nothing appropriate\" ]"
gen_py choose
check "choose foo or bar" "python choose.py foo bar |egrep -q '^privmsg: source: (foo|bar)\$'"

echo "passed: $passed, failed $failed"

if [ $failed -gt 0 ]; then
	exit 1
else
	rm -f $junk
	exit 0
fi
