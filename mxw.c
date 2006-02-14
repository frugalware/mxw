/*
 *  mxw.c for mxw
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
#include <inetlib.h>

#include "google.h"

#define NICK "mxw"
#define PASS "<2dA3xAkt"
#define USER "mxw"
#define SERVER "irc.freenode.net"
#define PORT 6667
#define CHANNEL "#fdb"

struct irc_server server0;

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
		_irc_raw_send(&server0, "PRIVMSG %s :%s: die plz (%s)\n", channel, from, content);
		free(channel);
	}
	else
	{
		_irc_raw_send(&server0, "PRIVMSG %s :die plz (%s)\n", from, content);
	}
	free(from);
}

int handle_privmsg(char *raw_data)
{
	char *from, *channel=NULL, *content;
	char *ptr;

	if((((ptr = getto(raw_data))!=NULL) && !strcmp(ptr, NICK)) || (!strchr(raw_data, '#')))
	{
		if(strchr(raw_data, '#')==NULL)
			from = getnick(raw_data);
		else
		{
			channel = getchannel(raw_data);
			from = getnick(raw_data);
		}
		content = getcontent(raw_data, channel);
		if(!strncmp(content, "google", strlen("google")))
			handle_google(channel, from, content);
		else
			handle_request(channel, from, content);
	}
	if(ptr)
		free(ptr);
	ptr=NULL;
	return(0);
}

void reconnect(void)
{
	irc_disconnect(&server0);
	irc_connect(&server0);
	_irc_raw_send(&server0, "privmsg NickServ :identify %s\n", server0.pass);
	usleep(2000000);
	_irc_raw_send(&server0, "join " CHANNEL "\n");
}

int main(void)
{
	int ret;

	server0.server = strdup(SERVER);
	server0.port = PORT;
	server0.nick = strdup(NICK);
	server0.user = strdup(USER);

	reconnect();

	while(1)
	{
		// wait till new data arrives, then get it
		ret = irc_receive(&server0, -1);

		if(ret > 0)
		{
			// for debugging
			printf("%s\n", server0.raw_data);
			if(strstr(server0.raw_data, "PRIVMSG"))
				handle_privmsg(server0.raw_data);

			// check for ping, and pong if necesary
			irc_check_ping(&server0);
		}
		if(ret < 0)
			reconnect();
	}
	return(0);
}
