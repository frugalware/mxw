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

if [ -z "$*" ]; then
	targets="t-*.sh"
else
	targets="$*"
fi

for i in $targets
do
	. $i
done

echo "passed: $passed, failed $failed"

if [ $failed -gt 0 ]; then
	exit 1
else
	rm -f $junk
	exit 0
fi
