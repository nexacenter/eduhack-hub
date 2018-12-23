L'hub per eduhack e` composto da un applicativo in flask e da uno scraper da schedulare con cron.
Tutte le funzioni non commentate sono ovvie.
La configurazione e` contenuta in config.py.

### Flask

L'applicativo di flask usa parti dello scraper come libreria.
L'applicativo dipende da sqlalchemy e jinja, un manager per i login e requests per validare le immagini.

Quasi ogni funzione definisce un endpoint:

```
/index/<int>/, GET: indice paginato dei post. 10 post alla volta.
/blogs/, GET: indice dei blog utenti, filtrati secondo config.py.
/submit, GET and POST: form per postare un link di un blog esterno.
/login GET and POST: serve per fare il login ed avere accesso agli endpoint successivi.

/admin GET and POST, login required: lista delle funzioni successive.
/remove_title, GET and POST, login required: form per rimuovere un titolo o una url dal database
/filter, GET and POST, login required: form per inserire o rimuovere dalla blacklist un domain o un URL 
```

Le pagine vengono rese attraverso l'uso di templates.
Header, includes e footer sono definite in base.html. E` uno schifo totale copiato da http://eduhack.eu/wall.

Consiglio di girare flask usando gunicorn e nginx come reverse proxy. Mysql (o meglio) per evitare i malditesta per le scritture concorrenti di sqlite.

### Scraper

Lo scraper e` fatto utilizzando requests, beautifulsoup e sqlalchemy per scrivere su db.

La lista dei siti dell'installazione di wordpress multisite non e` accessibile tramite api.
Per questo motivo lo scraper fa login utilizzando le credenziali provviste e con beautifulsoup parsa una lista dei blogs.
Una volta ottenuta la lista dei blog da parsare vengono utilizzate le api di wordpress senza autenticazione.
Gli endpoint utilizzati sono /posts, /users, /categories, /tags.
Tutti le url o i domini (`blogurl`) contenute in `urls_blacklist` o `domains_blacklist` vengono ignorate.
