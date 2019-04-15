In docker-compose.yml, bind a fixed IP address 172.28.0.2
Test: curl http://172.28.0.2:8000

In development mode, postgres is also in docker within the same network.
psydb.init_app(app=app, hostname="postgres")

