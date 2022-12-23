A tool to monitor a SteamWebPipes server for new releases and obtain the
corresponding appinfo in a time-critical manner storing it to disk for further
processing.

Required environment variables:

* ``APPINFO_DIR``: directory to store the appinfo files;
* ``STEAM_USER``: Steam user to log in as;
* ``STEAM_PASSWORD``: password for Steam user;
* ``STEAM_ID_BASE``: base offset for Steam login IDs to allow concurrent logins;
* ``WEB_PIPES_URL``: Websocket URL for a SteamWebPipes server.
