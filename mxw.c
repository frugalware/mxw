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

#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <inetlib.h>

#include "mxw.h"

struct irc_server server0;
char *reload_chan;

int main(void)
{
	void *handle;
	void *(*infop) (void);
	char cwd[PATH_MAX+1], *ptr;

	while(1)
	{
		// load the lib
		getcwd(cwd, PATH_MAX);
		asprintf(&ptr, "%s/libmxw.so", cwd);
		if ((handle = dlopen(ptr, RTLD_NOW)) == NULL)
		{
			fprintf(stderr, "%s\n", dlerror());
			return(1);
		}
		free(ptr);
		if ((infop = dlsym(handle, "info")) == NULL)
		{
			fprintf(stderr, "%s\n", dlerror());
			return(1);
		}
		lib_t *lib = infop();
		lib->handle = handle;

		if(!lib->run())
			return(0);

		dlclose(lib->handle);
	}
	return(0);
}
