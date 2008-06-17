gen_py isbn
check "isbn title" "python isbn.py 0156403005|sed -n 1p \
|grep -q \"^privmsg: His Master's Voice\$\""
check "isbn desc" "python isbn.py 0156403005|sed -n 2p \
|grep -q \"^privmsg: by Stanislaw Lem, Michael Kandel - Fiction - 1984 - 208 pages\$\""
check "isbn url" "python isbn.py 0156403005|sed -n 3p \
|grep -q \"^privmsg: http://books.google.com/books?id=uLFQAAAACAAJ&dq=isbn:0156403005\$\""
