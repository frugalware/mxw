typedef struct
{
	int (*run)(void);
	void *handle;
} lib_t;
