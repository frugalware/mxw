gen_py google
check "google title" "python google.py frugalware|sed -n 1p \
|grep -q \"^privmsg: Frugalware Linux - Let's make things Frugal!\$\""
check "google desc" "python google.py frugalware|sed -n 2p \
|grep -q \"^privmsg: Frugalware Linux, a general purpose linux distribution, designed for intermediate users.\$\""
check "google url" "python google.py frugalware|sed -n 3p \
|grep -q \"^privmsg: http://frugalware.org/\$\""
