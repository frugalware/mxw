/*	Google Web API
	Compile and run from the command line:
	googleapi <key> search|cached|spell <arg>
	where <key> is the Google API license key (see http://www.google.com/apis)
	Example:
	googleapi XXXXXXXX search gSOAP

Software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND,
either express or implied.

Copyright (C) 2002, Robert A. van Engelen, Florida State University.

*/

#include "soapH.h"
#include "googleapi.nsmap"
#include "google.h"

void *google(char *key, char *dir, char *arg)
{ struct soap soap;
  soap_init2(&soap, SOAP_IO_DEFAULT, SOAP_XML_TREE);
  if (!strcmp(dir, "search"))
  { struct api__doGoogleSearchResponse r;
    gsearch_t *search;
    if (soap_call_api__doGoogleSearch(&soap, "http://api.google.com/search/beta2", "urn:GoogleSearchAction", key, arg, 0, 10, true_, "", false_, "", "latin1", "latin1", &r))
    { soap_print_fault(&soap, stderr);
      return(NULL);
    }
    else
    {
        search = (gsearch_t*)malloc(sizeof(gsearch_t));
	memset(search, 0, sizeof(gsearch_t));
	if(r._return.resultElements.__ptr[0].title)
     		search->title = strdup(r._return.resultElements.__ptr[0].title);
	if(r._return.resultElements.__ptr[0].URL)
		search->url = strdup(r._return.resultElements.__ptr[0].URL);
	if(r._return.resultElements.__ptr[0].snippet)
		search->desc = strdup(r._return.resultElements.__ptr[0].snippet);
	return(search);
    }
  }
  else if (!strcmp(dir, "cached"))
  { struct xsd__base64Binary r;
    if (soap_call_api__doGetCachedPage(&soap, "http://api.google.com/search/beta2", "urn:GoogleSearchAction", key, arg, &r))
    { soap_print_fault(&soap, stderr);
      return(NULL);
    }
    else
    { int i;
      for (i = 0; i < r.__size; i++)
        putchar(r.__ptr[i]);
      putchar('\n');
    }
  }
  else if (!strcmp(dir, "spell"))
  { char *r;
    if (soap_call_api__doSpellingSuggestion(&soap, "http://api.google.com/search/beta2", "urn:GoogleSearchAction", key, arg, &r))
    { soap_print_fault(&soap, stderr);
      return(NULL);
    }
    else
      printf("Suggested spelling: %s\n", r?r:"<NONE>");
  }
  else
    fprintf(stderr, "Unknown directive\n");
  soap_end(&soap); /* remove all temporary and deserialized data */
  soap_done(&soap);
  return NULL;
}
