from app import app, db
from app.models import Actor, Medicine
from argparse import ArgumentParser
import os

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Actor': actor, 'Medicine': Medicine}


if __name__ == '__main__':
    parser = ArgumentParser()
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port, debug=True)
