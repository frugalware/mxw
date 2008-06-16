gen_py integrate
check "integrate" "[ \"\$(python integrate.py '(cos(x))^2')\" == \
	\"privmsg: http://integrals.wolfram.com/index.jsp?expr=%28cos%28x%29%29%5E2\" ]"
