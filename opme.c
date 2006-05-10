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

#include "config.h"

extern struct irc_server server0;

void handle_opme(char *channel, char *from, char *content)
{
	char *ptr;
	char buf[512];

	if(channel)
		ptr=channel;
	else
		ptr=from;
	if (strcmp(from, "vmiklos"))
	{
		_irc_raw_send(&server0, "PRIVMSG %s :Segmentation fault\n", ptr);
		return;
	}

	content += 5;

	snprintf(buf, 512, "MODE %s +o %s\n", CHANNEL, from);
	_irc_raw_send(&server0, buf);
}
