#include <stdio.h>
#include <string.h>
#include <mrss.h>
#include <inetlib.h>

#include "config.h"
#include "getdate.h"

extern struct irc_server server0;

int dorss (char *rss, char *target, char *channel, time_t *lastupd)
{
	mrss_t *data;
	mrss_error_t ret;
	mrss_item_t *item;
	char *ptr;

	if ((ret=mrss_parse_url(rss, &data)))
	{
		fprintf (stderr, "MRSS return error: %s\n", mrss_strerror (ret));
		return(1);
	}

	item = data->item;
	while (item)
	{
		// don't print any item for the first time
		if(*lastupd==0)
			break;
		if(get_date(item->pubDate, NULL)>*lastupd)
		{
			if(!strcmp(channel, "packages"))
			{
				if((ptr = strchr(item->author, '@')))
					*ptr='\0';
				// send the syncpkg'd packages to the bugs channel
				if(!strcmp(item->author, "syncpkgd"))
					_irc_raw_send(&server0, "PRIVMSG %s :14%s7 %s3 %s\n",
						BUGSCHAN, channel, item->author, item->title);
				else
					_irc_raw_send(&server0, "PRIVMSG %s :14%s7 %s3 %s\n",
						target, channel, item->author, item->title);
			}
			else if(!strcmp(channel, "ping"))
				_irc_raw_send(&server0, "PRIVMSG %s :14%s7 %s3 %s\n",
						target, channel, item->author, item->title);
			// blogs and bugs
			else
				_irc_raw_send(&server0, "PRIVMSG %s :14%s7 %s3 %s\n",
					target, channel, item->title, item->link);
		}
		item = item->next;
	}
	*lastupd=get_date(data->item->pubDate, NULL);
	mrss_free (data);
	return(0);
}
