import os
import sys
import tempfile

import pytest

#if os.path.abspath(os.curdir) not in sys.path:
#    sys.path.append(os.spath.abspath(os.curdisr))

from project import app, db


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        # Drop all of the existing database tables
        db.drop_all()
        # create the database and the database table
        db.create_all()

    yield client

    print("client end")
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/manage')
    print("res: ", rv)
    assert b'Test Managing Page Index' in rv.data