gen_py darcs
check "darcs without args" "python darcs.py|grep -q 'the following darcs repos are available'"
check "darcs with good arg" "python darcs.py darcsstats|grep -q 'darcs get --partial source@darcs.frugalware.org:/pub/other/darcsstats'"
check "darcs with bad arg" "python darcs.py foo |grep -q 'no such repo'"
