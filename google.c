/*
 *  google.c for mxw - USE ONLY FOR YOUR OWN!
 * 
 *  Copyright (c) 2007 by Miklos Vajna <vmiklos@frugalware.org>
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
#include <curl/curl.h>
#include <stdio.h>
#include <regex.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>

char curl_ret[PATH_MAX] = "";

static size_t curl_cb(void *ptr, size_t size, size_t nmemb, void *stream)
{
	char tmp[PATH_MAX], *p;
	p = strndup(ptr, size*nmemb);
	snprintf(tmp, PATH_MAX, "%s", curl_ret);
	snprintf(curl_ret, PATH_MAX, "%s%s", tmp, p);
	free(p);
	return(size*nmemb);
}

int google(char *params, char **title, char **desc, char **link)
{
	char url[PATH_MAX];

	curl_ret[0] = '\0';
	snprintf(url, PATH_MAX, "http://frugalware.org/~vmiklos/google/%s", params);
	CURL *easyhandle;
	if (curl_global_init(CURL_GLOBAL_ALL) != 0)
		return(-1);
	if ((easyhandle = curl_easy_init()) == NULL)
		return(-1);

	if (curl_easy_setopt(easyhandle, CURLOPT_WRITEFUNCTION, curl_cb) != 0)
		return(-1);
	if (curl_easy_setopt(easyhandle, CURLOPT_URL, url) != 0)
		return(-1);
	if (curl_easy_perform(easyhandle) != 0)
		return(-1);

	curl_easy_cleanup(easyhandle);
	curl_global_cleanup();
	if(strstr(curl_ret, "<html>"))
		return(-1);
	else
	{
		char *ptr;
		*title = curl_ret;
		if((ptr = strchr(*title, '\n')))
			*ptr++ = '\0';
		*desc = ptr;
		if((ptr = strchr(*desc, '\n')))
			*ptr++ = '\0';
		*link = ptr;
		if((ptr = strchr(*link, '\n')))
			*ptr = '\0';
		return(0);
	}
}

#if 0
int main(int argc, char **argv)
{
	char *title, *desc, *url;
	if (google("frugalware", &title, &desc, &url) == -1)
		printf("errors occured\n");
	else
	{
		printf("title: '%s'\n", title);
		printf("desc: '%s'\n", desc);
		printf("url: '%s'\n", url);
	}
	return(0);
}
#endif
