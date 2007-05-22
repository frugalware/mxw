/*
 *  xe.c for mxw - USE ONLY FOR YOUR OWN!
 *  see http://www.xe.com/errors/noautoextract.htm
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

/* match a string against a regular expression */

char *curl_ret;

static int match(char *string, char *pattern)
{
	int result;
	regex_t reg;

	if(regcomp(&reg, pattern, REG_EXTENDED | REG_NOSUB | REG_ICASE) != 0) {
		return(-1);
	}
	result = regexec(&reg, string, 0, 0, 0);
	regfree(&reg);
	return(!(result));
}

static size_t curl_cb(void *ptr, size_t size, size_t nmemb, void *stream)
{
	if(curl_ret)
		free(curl_ret);
	curl_ret = strndup(ptr, size*nmemb);
	return(size*nmemb);
}

char *xe(char *params)
{
	float amount;
	char from[PATH_MAX];
	char to[PATH_MAX];
	char url[PATH_MAX];

	if(sscanf(params, "%f %s in %s", &amount, from, to) != 3)
		return(NULL);
	snprintf(url, PATH_MAX, "http://frugalware.org/~vmiklos/xe/%f/%s/in/%s", amount, from, to);
	CURL *easyhandle;
	if (curl_global_init(CURL_GLOBAL_ALL) != 0)
		return(NULL);
	if ((easyhandle = curl_easy_init()) == NULL)
		return(NULL);

	if (curl_easy_setopt(easyhandle, CURLOPT_WRITEFUNCTION, curl_cb) != 0)
		return(NULL);
	if (curl_easy_setopt(easyhandle, CURLOPT_URL, url) != 0)
		return(NULL);
	curl_ret = NULL;
	if (curl_easy_perform(easyhandle) != 0)
		return(NULL);

	curl_easy_cleanup(easyhandle);
	curl_global_cleanup();
	if(!strncmp(curl_ret, "<!DOCTYPE HTML", strlen("<!DOCTYPE HTML")))
		return(NULL);
	else
		return(curl_ret);
}

int xe_check(char *str)
{
	return(match(str, "^[0-9.]+ [a-z]+ in [a-z]+$"));
}

#if 0
int main(int argc, char **argv)
{
	if(xe_check(argv[1]))
		printf("out: '%s'\n", xe(argv[1]));
}
#endif
