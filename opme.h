typedef struct __todo_t {
	char *cmd;
	char *owner;
} todo_t;
void handle_opme(char *channel, char *from, char *content);
void handle_voiceme(char *channel, char *from, char *content);
void handle_devoiceme(char *channel, char *from, char *content);
void handle_kick(char *channel, char *from, char *content);
void handle_voice(char *channel, char *from, char *content);
void handle_devoice(char *channel, char *from, char *content);
void handle_whois(char *raw);
void handle_join(char *raw_data);
