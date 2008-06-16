gen_py bugs
check "query existing bug" "[ \"\$(python bugs.py '#1')\" == \"privmsg: 14#17 Bug Report3 New7 Sample Task (Opened by Frugalware Buglist Admin)3 http://bugs.frugalware.org/1\" ]"
check "query non-existing bug" "[ \"\$(python bugs.py '#999999')\" == \"privmsg: no such bug\" ]"
