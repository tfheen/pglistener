from pglistener import PgListener

import bsddb

class NssDb(PgListener):
  def do_write(self,result,target):
    db = bsddb.btopen(target,"n")
    index = 0

    for row in result:
      name = row[0]
      id = row[2]
      entry = self.do_format(row) + '\0'

      db["".join([".", name])] = entry
      db["".join(["=", str(id)])] = entry
      db["".join(["0", str(index)])] = entry

      index += 1

    db.sync()
