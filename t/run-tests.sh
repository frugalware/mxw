#!/bin/bash

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
		echo -e " [\033[32mPASSED\033[0m]"
		passed=$(($passed+1))
	else
		echo -e " [\033[31mFAILED\033[0m]"
		failed=$(($failed+1))
		exit 1
	fi
}

if [ -z "$*" ]; then
	targets="t-*.sh"
else
	targets="$*"
fi

for i in $targets
do
	. ./$i
done

echo "passed: $passed, failed $failed"

rm -f $junk
exit 0
