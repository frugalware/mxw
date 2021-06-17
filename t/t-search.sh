gen_py db_search
check "db_search without args" "python3 db_search.py |grep -q 'rebase.*rtfm'"
check "db_search with good arg" "python3 db_search.py r[ef]b.se|grep -q 'rebase'"
check "db_search with bad arg" "python3 db_search.py rebasee |grep -q 'no matching records'"
