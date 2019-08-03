from app import db
from app.models import Actor, Medicine, Adress, Batch

meta = db.metadata
for table in reversed(meta.sorted_tables):
    print ('Clear table %s' % table)
    db.session.execute(table.delete())
db.session.commit()
