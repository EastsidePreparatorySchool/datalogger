from src import init_app #, request, json, db


app = init_app()

if __name__ == '__app__':
      app.run(debug = True) #app.run(host, prot, debug, options)

#SQlite https://blog.appseed.us/flask-how-to-connect-to-mysql/
#.\Script\activate to get the app env set up
#$env:FLASK_APP = "main"
#flask shell #gets a shell to the app
