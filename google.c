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
#include <curl/curl.h>
#include <inetlib.h>

extern struct irc_server server0;

int download(char *from, char *to)
{
	CURL *easyhandle;
	FILE *fp;

	if ((fp = fopen(to, "w")) == NULL)
	{
		perror("could not open file for writing");
		return(1);
	}
	
	if (curl_global_init(CURL_GLOBAL_ALL) != 0)
		return(1);
	if ((easyhandle = curl_easy_init()) == NULL)
		return(1);

	if (curl_easy_setopt(easyhandle, CURLOPT_VERBOSE, 1) != 0)
		return(1);
	if (curl_easy_setopt(easyhandle, CURLOPT_WRITEDATA, fp) != 0)
		return(1);
	if (curl_easy_setopt(easyhandle, CURLOPT_URL, from) != 0)
		return(1);
	if (curl_easy_perform(easyhandle) != 0)
		return(1);
	
	curl_easy_cleanup(easyhandle);
	curl_global_cleanup();
	return(0);
}

unsigned char *urlencode(unsigned char *s)
{
	unsigned char *t, *p, *tp;

	if(s == NULL)
		return(NULL);
	t = (unsigned char*)malloc(strlen((char*)s)*3+1);

	tp=t;
	for(p=s; *p; p++)
	{
		if((*p > 0x00 && *p < ',') ||
			(*p > '9' && *p < 'A') ||
			(*p > 'Z' && *p < '_') ||
			(*p > '_' && *p < 'a') ||
			(*p > 'z' && *p < 0xA1))
		{
			sprintf((char*)tp, "%%%02X", *p);
			tp += 3;
		}
		else
		{
			*tp = *p;
			tp++;
		}
	}
	*tp='\0';
	return(t);
}

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

void handle_google(char *channel, char *from, char *content)
{
	FILE *fp;
	char line[4097], *ptr, *ptr2;
	char *tmpfile, *url, *title, *desc;

	content += 7;
	ptr = (char*)urlencode((unsigned char*)content);
	tmpfile = strdup("/tmp/mxw_XXXXXX");
	mkstemp(tmpfile);
	asprintf(&ptr2, "http://www.google.co.hu/search?q=%s", ptr);
	if(download(ptr2, tmpfile))
	{
		free(ptr);
		free(ptr2);
		unlink(tmpfile);
		free(tmpfile);
		return;
	}
	free(ptr);
	free(ptr2);

	fp = fopen(tmpfile, "r");
	while(!feof(fp))
	{
		memset(line, 0, 4096);
		fread(line, 1, 4096, fp);
		if((ptr=strstr(line, "<p class=g>")))
		{
			ptr = strstr(ptr, "href=\"");
			url = strdup(ptr + 6);
			ptr2 = strstr(url, "\">");
			*ptr2='\0';

			ptr = strstr(ptr, "\">");
			title = strdup(ptr+2);
			ptr2 = strstr(title, "</a>");
			*ptr2='\0';
			ptr2 = bold2irc(title);
			free(title);
			title = ptr2;

			ptr = strstr(ptr, "=-1>");
			desc = strdup(ptr+4);
			ptr2 = strstr(desc, "<br>");
			ptr2 += 4;
			ptr2 = strstr(ptr2, "<br>");
			*ptr2='\0';
			ptr2 = bold2irc(desc);
			free(desc);
			desc = ptr2;

			if(channel)
				ptr=channel;
			else
				ptr=from;
				_irc_raw_send(&server0, "PRIVMSG %s :((google)) %s\n", ptr, title);
				ptr2=desc;
				_irc_raw_send(&server0, "PRIVMSG %s :%s\n", ptr, desc);
				while((ptr2=strchr(ptr2, '\n')))
				{
					ptr2++;
					_irc_raw_send(&server0, "PRIVMSG %s :%s\n", ptr, ptr2);
				}
				_irc_raw_send(&server0, "PRIVMSG %s :%s\n", ptr, url);
			if(channel)
				free(channel);
			free(from);
			free(url);
			free(title);
			free(desc);
			break;
		}
	}
	fclose(fp);
	unlink(tmpfile);
	free(tmpfile);
}
