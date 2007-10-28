import socket, sys

client = socket.socket ( socket.AF_UNIX, socket.SOCK_DGRAM )
client.connect ("mxw2.sock")
client.send ("""c.privmsg("%s", "%s")""" % (sys.argv[1], sys.argv[2]))
#client.send ("""c.disconnect("reconnecting")""")
client.close()
