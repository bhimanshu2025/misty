from flasky import create_app 

app = create_app() 
# had to load below mistobj here since loading it in the create_app was creating circular import issues
with app.app_context():
    from flasky.utils.utilities import MistObj
    app.config['MIST_OBJ'] = MistObj()
if __name__ == "__main__":
    app.run()