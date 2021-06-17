gen_py db
check "db without args" "python3 db.py |grep -q \": 'db' requires a parameter\""
check "db with good arg" "python3 db.py rebase|grep -q \": rebase => git config branch.master.rebase true\""
check "db with bad arg" "[ -z \"\$(python3 db.py rebasee)\" ]"
