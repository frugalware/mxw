/*
 *  libmxw.c for mxw
 * 
 *  Copyright (c) 2006 by Miklos Vajna <vmiklos@frugalware.org>
 * 
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, 
 *  USA.
 */

#include <time.h>
#include <signal.h>
#include <inetlib.h>

#include "mxw.h"
#include "google.h"
#include "eval.h"
#include "opme.h"
#include "libmxw.h"
#include "config.h"
#include "rss.h"
#include "xe.h"
#include "bc.h"

extern struct irc_server server0;
extern char *reload_chan;

lib_t lib =
{
	run,
	NULL // dlopen handle
};

lib_t *info()
{
	 return &lib;
}

void cleanup(int signum)
{
	_irc_raw_send(&server0, "QUIT\n");
	exit(signum);
}

char *getchannel(char *data)
{
	char buf[BUF_SIZE];
	char *str, *ptr;

	strcpy(buf, data);
	str = buf;
	str = strchr(++str, ' ');
	str = strchr(++str, ' ');
	ptr = strchr(++str, ' ');
	*ptr = '\0';

	return(strdup(str));
}

char *getto(char *data)
{
	char buf[BUF_SIZE];
	char *str, *ptr;

	strcpy(buf, data);
	str = buf;
	str = strchr(++str, ' ');
	str = strchr(++str, ' ');
	str = strchr(++str, ' ');
	ptr = strchr(++str, ' ');
	if(ptr)
		*--ptr = '\0';
	else
		return(NULL);

	return(strdup(++str));
}

char *getnick(char *data)
{
	char buf[BUF_SIZE];
	char *str, *ptr;

	strcpy(buf, data);
	str = buf;
	ptr = strchr(++str, '!');
	*ptr = '\0';

	return(strdup(str));
}

char *getcontent(char *data, char *channel)
{
	char *ptr;
	int i;

	ptr = data;
	for(i=0;i<3&&ptr;i++)
		ptr = strchr(++ptr, ' ');
	if(channel!=NULL)
		ptr = strchr(++ptr, ' ');
	else
		ptr++;

	return(++ptr);
}

void handle_request(char *channel, char *from, char *content)
{
	if(channel)
	{
		_irc_raw_send(&server0, "PRIVMSG %s :%s: hi!\n", channel, from);
		free(channel);
	}
	else
	{
		_irc_raw_send(&server0, "PRIVMSG %s :hi!\n", from);
	}
	free(from);
}

void handle_negative(char *channel, char *from, char *content)
{
	if(channel)
	{
		_irc_raw_send(&server0, "PRIVMSG %s :%s: nope\n", channel, from);
		free(channel);
	}
	else
	{
		_irc_raw_send(&server0, "PRIVMSG %s :nope\n", from);
	}
	free(from);
}

void handle_threedot(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: using \"...\" so much isn't "
			"polite to other users. please consider changing that "
			"habit.\n", channel, from);
}

void handle_usehu(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: nem, viccbol van belole csomag\n",
			channel, from);
}

void handle_au(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: 22:13 -!- Mojojojo [n=Mojojojo@reaktor.linuxforum.hu] has quit [Read error: 104 (Connection reset by peer)]\n", channel, from);
}

void handle_bugs(char *channel, char *from, char *name)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: %s => here we can help, but if you want a bug/feature "
		"to be fixed/implemented, then please file a bugreport/feature request at "
		"http://bugs.frugalware.org\n", channel, from, name);
}

void handle_rtfm(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: rtfm => if you're new to Frugalware, then before asking please read our documentation at http://frugalware.org/docs/, probably your question is answered there\n", channel, from);
}

void handle_flame(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :%s: flame => Frugalware is best! All other distros suck! Oh, sure, we plan to take over the world any minute now ;)\n", channel, from);
}

void handle_dance(char *channel, char *from)
{
	_irc_raw_send(&server0, "PRIVMSG %s :0-<\n", channel);
	_irc_raw_send(&server0, "PRIVMSG %s :0-/\n", channel);
	_irc_raw_send(&server0, "PRIVMSG %s :0-\\\n", channel);
}

void handle_smiley(char *channel, char *from, int mode)
{
	if(mode==0)
		_irc_raw_send(&server0, "PRIVMSG %s :%s: :D\n", channel, from);
	else if(mode==1)
		_irc_raw_send(&server0, "PRIVMSG %s :%s: lol\n", channel, from);
}

int handle_privmsg(char *raw_data)
{
	char *from, *channel=NULL, *content;
	char *ptr;

	if((((ptr = getto(raw_data))!=NULL) && !strcmp(ptr, NICK)) || (!strstr(raw_data, "PRIVMSG #")))
	{
		if(!strstr(raw_data, "PRIVMSG #"))
			from = getnick(raw_data);
		else
		{
			channel = getchannel(raw_data);
			from = getnick(raw_data);
		}
		content = getcontent(raw_data, channel);
		if(!strncmp(content, "google", strlen("google")))
		{
			char *title, *desc, *url, *ptr;
			ptr = content;
			if((ptr = strchr(content, ' ')))
					ptr++;
			if (google(ptr, &title, &desc, &url) == -1)
				_irc_raw_send(&server0, "PRIVMSG %s :google: ping\n", channel);
			else
			{
				if(title)
					_irc_raw_send(&server0, "PRIVMSG %s :((google)) %s\n", channel, title);
				if(desc)
					_irc_raw_send(&server0, "PRIVMSG %s :%s\n", channel, desc);
				if(url)
					_irc_raw_send(&server0, "PRIVMSG %s :%s\n", channel, url);
			}
		}
		else if(!strncmp(content, "reload", strlen("reload")))
		{
			reload_chan = strdup(channel);
			return(1);
		}
		else if(!strncmp(content, "eval", strlen("eval")))
			handle_eval(channel, from, content, MASTER);
		else if(!strncmp(content, "opme", strlen("opme")))
			handle_opme(channel, from, content);
		else if(!strncmp(content, "voiceme", strlen("voiceme")))
			handle_voiceme(channel, from, content);
		else if(!strncmp(content, "devoiceme", strlen("devoiceme")))
			handle_devoiceme(channel, from, content);
		else if(!strncmp(content, "kick", strlen("kick")))
			handle_kick(channel, from, content);
		else if(!strncmp(content, "voice", strlen("voice")))
			handle_voice(channel, from, content);
		else if(!strncmp(content, "devoice", strlen("devoice")))
			handle_devoice(channel, from, content);
		else if(!strncmp(content, "bugs", strlen("bugs")))
			handle_bugs(channel, from, "bugs");
		else if(!strncmp(content, "bts", strlen("bts")))
			handle_bugs(channel, from, "bts");
		else if(!strncmp(content, "rtfm", strlen("rtfm")))
			handle_rtfm(channel, from);
		else if(!strncmp(content, "flame", strlen("flame")))
			handle_flame(channel, from);
		else if(!strncmp(content, "dance", strlen("dance")))
			handle_dance(channel, from);
		else if(!strncmp(content, ":)", strlen(":)")))
			handle_smiley(channel, from, 0);
		else if(!strncmp(content, ":D", strlen(":D")))
			handle_smiley(channel, from, 1);
		else if(!strncmp(content, "ping", strlen("ping")))
			_irc_raw_send(&server0, "PRIVMSG %s :pong\n", channel);
		else if(xe_check(content))
		{
			ptr = xe(content);
			if(ptr)
			{
				_irc_raw_send(&server0, "PRIVMSG %s :%s: %s\n", channel, from, ptr);
			}
			else
				_irc_raw_send(&server0, "PRIVMSG %s :xe.com hates me ;/\n", channel);
		}
		else if(bc_check(content))
		{
			ptr = bc(content);
			if(ptr)
			{
				_irc_raw_send(&server0, "PRIVMSG %s :%s: %s\n", channel, from, ptr);
			}
			else
				_irc_raw_send(&server0, "PRIVMSG %s :%s: bc says you're stupid\n", channel, from);
		}
		else if(strstr(content, "suck"))
			handle_negative(channel, from, content);
		else
			handle_request(channel, from, content);
	}
	else if(strstr(raw_data, "PRIVMSG " CHANNEL " "))
	{
		from = getnick(raw_data);
		content = strstr(raw_data, CHANNEL);
		content += strlen(CHANNEL);
		if(strstr(content, " ... "))
			handle_threedot(CHANNEL, from);
		free(from);
	}
	else if(strstr(raw_data, "PRIVMSG #frugalware.hu "))
	{
		from = getnick(raw_data);
		content = strstr(raw_data, "#frugalware.hu");
		content += strlen("#frugalware.hu");
		if(strstr(content, " :hasznal valaki"))
			handle_usehu("#frugalware.hu", from);
		free(from);
	}
	if(ptr)
		free(ptr);
	ptr=NULL;
	return(0);
}

void reconnect(void)
{
	server0.server = strdup(SERVER);
	server0.port = PORT;
	server0.nick = strdup(NICK);
	server0.user = strdup(USER);
	server0.pass = strdup(PASS);

	irc_disconnect(&server0);
	irc_connect(&server0);
	_irc_raw_send(&server0, "privmsg NickServ :identify %s\n", server0.pass);
	usleep(4000000);
	_irc_raw_send(&server0, "join " CHANNEL "\n");
	_irc_raw_send(&server0, "join " CHANNEL2 "\n");
	_irc_raw_send(&server0, "join " CHANNEL3 "\n");
	_irc_raw_send(&server0, "join " CHANNEL4 "\n");
	_irc_raw_send(&server0, "join " CHANNEL5 "\n");
}

void check_rss(void)
{
	static time_t packages=0, blogs=0, bugs=0, monit=0;
	static time_t lastupd=0;
	time_t current = time(NULL);

	if(!lastupd)
		lastupd=time(NULL);
	if((lastupd!=current) && ((current-lastupd)<180))
		return;
	lastupd = current;
	dorss("http://frugalware.org/rss/packages", PACKAGESCHAN, "packages", &packages);
	dorss("http://frugalware.org/rss/blogs", BLOGSCHAN, "blogs", &blogs);
	dorss("http://frugalware.org/rss/bugs", BUGSCHAN, "bugs", &bugs);
	dorss("http://frugalware.org/~vmiklos/ping2rss/ping2rss.py", MONITCHAN, "ping", &monit);
}

int run(void)
{
	int ret, myret=0;

	/* set signal handlers */
	signal(SIGINT, cleanup);
	signal(SIGTERM, cleanup);
	signal(SIGSEGV, cleanup);

	if(!server0.server)
		reconnect();
	else
	{
		_irc_raw_send(&server0, "privmsg %s :reload done\n", reload_chan);
		free(reload_chan);
	}

	while(1)
	{
		// wait till new data arrives, then get it
		ret = irc_receive(&server0, 300);

		if(ret > 0)
		{
			// for debugging
			printf("%s\n", server0.raw_data);
			handle_whois(server0.raw_data);
			if(strstr(server0.raw_data, "PRIVMSG"))
				myret += handle_privmsg(server0.raw_data);
			if(strstr(server0.raw_data, "JOIN"))
				handle_join(server0.raw_data);

			// check for ping, and pong if necesary
			irc_check_ping(&server0);
			check_rss();
		}
		if(ret < 0)
			reconnect();
		if(myret)
			break;
	}
	return(myret);
}
