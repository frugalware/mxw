gen_py dict
check "dict hu2en" "python dict.py hu2en ember|sed -n 1p \
|grep -q \"^privmsg: ember: bleeder; man, men; mortal; number; person; soul; walla; wallah\$\""
