/*
 *  opme.c for mxw
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
#include <stdlib.h>
#include <libxml/xmlmemory.h>
#include <libxml/parser.h>
#include <glib.h>

#include "config.h"
#include "libmxw.h"
#include "opme.h"

extern struct irc_server server0;

GList *todo=NULL;

int checkAuthor(xmlDoc *doc, xmlNode *cur, char *nick)
{
	xmlChar *key;
	cur = cur->xmlChildrenNode;

	while (cur != NULL)
	{
		key = xmlNodeListGetString(doc, cur->xmlChildrenNode, 1);
		if ((!xmlStrcmp(cur->name, (const xmlChar *)"nick")))
		{
			if ((!xmlStrcmp(key, (const xmlChar *)nick)))
			{
				xmlFree(key);
				return(1);
			}
		}
		xmlFree(key);
		cur = cur->next;
	}
	return(0);
}

int checkAuthors(char *nick)
{
	xmlDocPtr doc;
	xmlNodePtr cur;

	doc = xmlParseFile(AUTHORSFILE);

	if(doc == NULL)
	{
		fprintf(stderr, "document not parsed successfully\n");
		return(0);
	}

	cur = xmlDocGetRootElement(doc);

	if(cur == NULL)
	{
		fprintf(stderr, "empty document\n");
		xmlFreeDoc(doc);
		return(0);
	}

	if(xmlStrcmp(cur->name, (const xmlChar *)"authors"))
	{
		fprintf(stderr, "document of the wrong type, root node != authors");
		xmlFreeDoc(doc);
		return(0);
	}

	cur = cur->xmlChildrenNode;
	while(cur != NULL)
	{
		if((!xmlStrcmp(cur->name, (const xmlChar *)"author")))
			if(checkAuthor(doc, cur, nick))
			{
				xmlFreeDoc(doc);
				return(1);
			}
		cur = cur->next;
	}

	xmlFreeDoc(doc);
	return(0);
}
void handle_opme(char *channel, char *from, char *content)
{
	char *ptr;
	todo_t *t;

	if(channel)
		ptr=channel;
	else
		ptr=from;
	if (!checkAuthors(from))
	{
		_irc_raw_send(&server0, "PRIVMSG %s :Segmentation fault\n", ptr);
		return;
	}

	if((t = (todo_t *)malloc(sizeof(todo_t))) == NULL)
		return;

	t->owner = strdup(from);
	t->cmd = g_strdup_printf("MODE %s +o %s", ptr, from);
	todo = g_list_append(todo, t);

	_irc_raw_send(&server0, "WHOIS %s\n", from);
}

void handle_voiceme(char *channel, char *from, char *content)
{
	char *ptr;
	todo_t *t;

	if(channel)
		ptr=channel;
	else
		ptr=from;
	if (!checkAuthors(from))
	{
		_irc_raw_send(&server0, "PRIVMSG %s :u r t3h w4nn4b3\n", ptr);
		return;
	}

	if((t = (todo_t *)malloc(sizeof(todo_t))) == NULL)
		return;

	t->owner = strdup(from);
	t->cmd = g_strdup_printf("MODE %s +v %s", ptr, from);
	todo = g_list_append(todo, t);

	_irc_raw_send(&server0, "WHOIS %s\n", from);
}

void handle_devoiceme(char *channel, char *from, char *content)
{
	char *ptr;
	todo_t *t;

	if(channel)
		ptr=channel;
	else
		ptr=from;
	if (!checkAuthors(from))
	{
		_irc_raw_send(&server0, "PRIVMSG %s :(null)\n", ptr);
		return;
	}

	if((t = (todo_t *)malloc(sizeof(todo_t))) == NULL)
		return;

	t->owner = strdup(from);
	t->cmd = g_strdup_printf("MODE %s -v %s", ptr, from);
	todo = g_list_append(todo, t);

	_irc_raw_send(&server0, "WHOIS %s\n", from);
}

void handle_kick(char *channel, char *from, char *content)
{
	char *who, *why, *ptr;
	todo_t *t;

	who = strdup(content+strlen("kick "));
	if((ptr = strstr(who, " ")))
		*ptr = '\0';

	// 3 for the 3 spaces: " kick nick "
	if(strlen(content)>strlen("kick")+strlen(from)+3)
		why = strdup(content+strlen("kick")+strlen(from)+3);
	else
		why = strdup("can't we all be friends?");

	if(!channel)
		channel=from;
	if (!checkAuthors(from))
	{
		_irc_raw_send(&server0, "PRIVMSG %s :%s: haha\n", channel, from);
		return;
	}

	if((t = (todo_t *)malloc(sizeof(todo_t))) == NULL)
		return;

	t->owner = strdup(from);
	t->cmd = g_strdup_printf("KICK %s %s :%s", channel, who, why);
	todo = g_list_append(todo, t);
	free(who);
	free(why);

	_irc_raw_send(&server0, "WHOIS %s\n", from);
}

void handle_join(char *raw_data)
{
	char *from = getnick(raw_data);

	if(strstr(raw_data, "JOIN :" CHANNEL2))
	{
		if (checkAuthors(from))
		{
			todo_t *t;

			if((t = (todo_t *)malloc(sizeof(todo_t))) == NULL)
				return;
			t->owner = strdup(from);
			t->cmd = g_strdup_printf("MODE %s +v %s", CHANNEL2, from);
			todo = g_list_append(todo, t);
			_irc_raw_send(&server0, "WHOIS %s\n", from);
		}
	}
}

void handle_whois(char *raw)
{
	char *ptr, *nick;
	int i;

	if((ptr=strstr(raw, "320 " NICK)))
	{
		nick = strdup(ptr+strlen(NICK)+5);
		ptr = nick;
		while(*ptr!=' ')
			ptr++;
		*ptr='\0';
		for(i=0;i<g_list_length(todo);i++)
		{
			todo_t *t = g_list_nth_data(todo, i);
			if(!strcmp(t->owner, nick))
			{
				_irc_raw_send(&server0, "%s\n", t->cmd);
				free(t->owner);
				free(t->cmd);
				todo = g_list_remove(todo, t);
			}
		}
		free(nick);
	}
}
