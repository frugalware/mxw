typedef struct __todo_t {
	char *cmd;
	char *owner;
} todo_t;
void handle_opme(char *channel, char *from, char *content);
void handle_whois(char *raw);
void handle_join(char *raw_data);
