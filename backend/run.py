# run.py

#from project import app

from project import create_app 
app = create_app()

if __name__ == "__main__":
    app.run(use_reloader=True)
    #print(os.environ["FLASK_DEBUG"])
