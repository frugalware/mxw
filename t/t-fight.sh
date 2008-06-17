gen_py fight
check "fight" "python fight.py frugalware frugalwarez \
|grep -q \"^privmsg: googlefight: frugalware wins! [0-9]\+ vs [0-9]\+\$\""
