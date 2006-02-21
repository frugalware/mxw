/*
 *  google.c for mxw
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

#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <inetlib.h>
#include <google.h>

extern struct irc_server server0;

char *bold2irc(char *from)
{
	char *ret, *ptr;

	ret = strdup(from);
	while((ptr=strstr(ret, "<b>")))
	{
		*ptr='';
		memmove(ptr+1, ptr+3, strlen(ptr)-2);
	}
	while((ptr=strstr(ret, "</b>")))
	{
		*ptr='';
		memmove(ptr+1, ptr+4, strlen(ptr)-3);
	}
	while((ptr=strstr(ret, "<br>")))
	{
		memmove(ptr, ptr+4, strlen(ptr)-3);
	}
	return(ret);
}

void handle_spell(char *channel, char *from, char *content, char *key)
{
	char *ptr;

	content += 6;
	ptr = (char*)google(key, "spell", content);
	if(ptr==NULL)
	{
		if(channel)
			_irc_raw_send(&server0, "PRIVMSG %s :%s: hey, what's the problem here?\n", channel, from);
		else
			_irc_raw_send(&server0, "PRIVMSG %s :hey, what's the problem here?\n", from);
	}
	else
	{
		if(channel)
			_irc_raw_send(&server0, "PRIVMSG %s :%s: %s, moron!\n", channel, from, ptr);
		else
			_irc_raw_send(&server0, "PRIVMSG %s :%s, moron!\n", from, ptr);
	}
	if(ptr)
		free(ptr);
}

void handle_google(char *channel, char *from, char *content, char *key)
{
	char *ptr;
	char *title=NULL, *desc=NULL;

	content += 7;
	gsearch_t *s = google(key, "search", content);
	if(channel)
		ptr=channel;
	else
		ptr=from;
	if(s == NULL)
	{
		_irc_raw_send(&server0, "PRIVMSG %s :google: ping\n", ptr);
		return;
	}
	if(s->title == NULL)
	{
		_irc_raw_send(&server0, "PRIVMSG %s :lol @ u\n", ptr);
		return;
	}
	if(s->title)
		title = bold2irc(s->title);
	if(s->desc)
		desc = bold2irc(s->desc);

			if(title)
				_irc_raw_send(&server0, "PRIVMSG %s :((google)) %s\n", ptr, title);
			if(desc)
				_irc_raw_send(&server0, "PRIVMSG %s :%s\n", ptr, desc);
			if(s->url)
				_irc_raw_send(&server0, "PRIVMSG %s :%s\n", ptr, s->url);
			if(channel)
				free(channel);
			free(from);
			free(title);
			free(desc);
			free(s->title);
			free(s->desc);
			free(s->url);
			free(s);
}
