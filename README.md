# Dipendenze

```
apt install nginx git python3-pip sqlite3 # root
cat requirements.txt | xargs pip3 install --user  # with the right user
```
 

L'hub per eduhack e\` composto da un applicativo in flask e da uno scraper da schedulare con cron.
L'interfaccia di admin si raggiunge tramite <url>/admin, la password e\` contenuta in conf.py
Tutte le funzioni non commentate sono ovvie.
La configurazione e\` contenuta in config.py.

# Flask

L'applicativo di flask usa parti dello scraper come libreria.
L'applicativo dipende da sqlalchemy e jinja, un manager per i login e requests per validare le immagini.

Quasi ogni funzione definisce un endpoint:

```
/index/<int>/, GET: indice paginato dei post. 10 post alla volta.
/blogs/, GET: indice dei blog utenti, filtrati secondo config.py.
/submit, GET and POST: form per postare un link di un blog esterno.
/search, GET and POST: form per cercare posts per tags o categories
/tag/<int>/, GET: ritorna i post con quel tagid.
/categories/<int>/, GET: ritorna i post con quel categoriesid.
/login GET and POST: serve per fare il login ed avere accesso agli endpoint successivi.

/admin GET and POST, login richiesto: lista delle funzioni successive.
/remove_title, GET and POST, login richiesto: form per rimuovere un titolo o una url dal database
/filter, GET and POST, login richiesto: form per inserire o rimuovere dalla blacklist un domain o un URL 
```

Le pagine vengono rese attraverso l'uso di templates.
Header, includes e footer sono definite in base.html. E\` uno schifo totale copiato da http://eduhack.eu/wall.

Consiglio di girare flask usando gunicorn e nginx come reverse proxy. Mysql (o meglio) per evitare i malditesta per le scritture concorrenti di sqlite.


# Scraper

Lo scraper e\` fatto utilizzando requests, beautifulsoup e sqlalchemy per scrivere su db.

La lista dei siti dell'installazione di wordpress multisite non e\` accessibile tramite api.
Per questo motivo lo scraper fa login utilizzando le credenziali provviste e con beautifulsoup parsa una lista dei blogs.
Una volta ottenuta la lista dei blog da parsare vengono utilizzate le api di wordpress senza autenticazione.
Gli endpoint utilizzati sono /posts, /users, /categories, /tags.
Tutti le url o i domini (`blogurl`) contenute in `urls_blacklist` o `domains_blacklist` vengono ignorate.

# Deploy

### Gunicorn

Gunicorn e\` molto semplice da avviare:
` gunicorn app:app -b localhost:8000 -w N `
dove N sono il numero di workers e app si riferisce al modulo app.py della root directory del progetto.
Gunicorn non logga gli errori di app.py ma lascia che l'output venga stampato. Si consiglia di ridirezionare stdout e stderr.

### NGINX

Nginx viene usato come reverse proxy.
In caso si preferisca usare apache2 senza fare reverse_proxy bisogna configurare qualche mod per python e poi usare app.py come cgi.
```
server {
    listen   80; # The default is 80 but this here if you want to change it.
    server_name hub.eduhack.eu;
    
    location / {
        proxy_pass              http://localhost:<port>;
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout   150;
        proxy_send_timeout      100;
        proxy_read_timeout      100;
        proxy_buffers           4 32k;
        client_max_body_size    500m; # Big number is we can post big commits.
        client_body_buffer_size 128k;
    }
}
```

Si possono pensare strategie di caching:

```
   location ~* \.(ico|css|js|jpg|png|)$ {
       expires 1d;
       access_log off;
       add_header Pragma public;
       add_header Cache-Control "public, max-age=86400";
       add_header X-Asset "yes";
   }
```

### Systemd

Si suppone che al Nexa venga ancora usato systemd.
`path: /etc/systemd/system/`
`systemctl enable hub.service`

Si devono sostituire le variabili chiaramente!

```
[Unit]
Description=EduHack hub
After=network.target

[Service]
Type=simple
User=<user>
WorkingDirectory=/home/<user>/<path to repo>
ExecStart=</PATH_TO_local/bin/>gunicorn  --options
Restart=on-failure
# oppure: or always, on-abort, etc

[Install]
WantedBy=multi-user.target
```

### Scraper / cron
Lo scraper va eseguito secondo un intervallo di tempo (esempio 30 minuti).
``` cron
0,30 * * * * python3 /path/scrape.py > /logpath/scrape.log 2>&1
```
In alternative si puo` usare systemd con un timer:

`https://unix.stackexchange.com/questions/198444/run-script-every-30-min-with-systemd`

# File di configurazione

In config.py sono contenuti vari parametri di configurazione.
```
password = 'prova' # il codice di autenticazione per accedere alle funzioni di amministrazione
secret = '123upudnpomi8r2yn' # un secret code per flask, puo` essere generato casualmente e viene utilizzato per le sessioni
db = 'sqlite:///edu.db' # URI del db per sqlalchemy. Considerare: "mysql+pymysql://user:passwd@localhost/nomedb",
wp_pwd = 'provaprova2' # password per accedere a wordpress
email = 'me@francescomecca.eu' # email da usare come username per wordpress
do_not_list = ['test', 'admin', 'atester'] # blogs that should not displayed in /blogs
```

#### Considerazioni

Il codice e\` il risultato dell'imposizione di deadline stringente.
Se si volesse migliorarlo vedi il seguente schema:

1. Portare i file di blacklist dentro il db
2. muovere i moduli dentro una cartella propria
3. usare sqlalchemy per le query invece di query testuali 
4. creare un endpoint per la lista dei blog in php in modo da poterci accedere tramite le api rest
5. impostare l'autenticazione per le api di wp
6. il codice e\` abbastanza leggibile ma alcune funzioni vanno spostati in moduli (principalmente login e inizializzazione)
7. il codice e\` abbastanza leggibile ma si puo\` fare refactoring di codice duplicato
