/*
 *  bc.c for mxw
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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <wait.h>
#include <regex.h>
#include <string.h>

/* match a string against a regular expression */

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

static int popen2(char **args, FILE **fpin, FILE **fpout)
{
	int pin[2], pout[2];
	pid_t pid;

	if(pipe(pin) == -1)
	{
		perror("pipe");
		return(-1);
	}
	if(pipe(pout) == -1)
	{
		perror("pipe");
		return(-1);
	}

	pid = fork();
	if(pid == -1)
	{
		perror("fork");
		return(-1);
	}
	if (pid == 0) {
		/* we are "in" the child */

		/* this process' stdin should be the read end of the pin pipe.
		 * dup2 closes original stdin */
		dup2(pin[0], STDIN_FILENO);
		close(pin[0]);
		close(pin[1]);
		dup2(pout[1], STDOUT_FILENO);
		/* this process' stdout should be the write end of the pout
		 * pipe. dup2 closes original stdout */
		close(pout[1]);
		close(pout[0]);

		execv(args[0], args);
		/* on sucess, execv never returns */
		return(-1);
	}

	close(pin[0]);
	close(pout[1]);
	*fpin = fdopen(pin[1], "w");
	*fpout = fdopen(pout[0], "r");
	return(0);
}

char *bc(char *params)
{
	FILE *pin, *pout;
	char buf[256] = "";
	char *args[] = { "/usr/bin/bc", NULL };

	if(popen2(args, &pin, &pout) == -1)
		return(NULL);

	params += strlen("calc ");
	fprintf(pin, "%s\n", params);
	fclose(pin);

	fgets(buf, 255, pout);
	if(buf)
		buf[strlen(buf)-1]='\0';
	fclose(pout);

	if(!strlen(buf))
		return(NULL);
	return(strdup(buf));
}

int bc_check(char *str)
{
	return(match(str, "^calc "));
}

#if 0
int main(int argc, char **argv)
{
	if(bc_check(argv[1]))
		printf("out: '%s'\n", bc(argv[1]));
	return(0);
}
#endif
