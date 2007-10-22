from pglistener import PgListener

import bsddb

class NssDb(PgListener):
  def do_write(self,result,target):
    db_keys = self.options['db-keys']
    db = bsddb.btopen(target,"n")
    index = 0

    for row in result:
      entry = self.do_format(row) + '\0'

      for field in db_keys.keys():
        db[db_keys[field] % row[field]] = entry

      db["0%d" % index] = entry

      index += 1

    db.sync()
