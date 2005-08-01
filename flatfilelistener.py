from pglistener import PgListener

class FlatFileListener(PgListener):
  def __init__(self,options):
    if(not options.has_key('delimeter')):
      options['delimeter']=' '
    PgListener.__init__(self,options)

  def do_format(self,row):
    return self.options['delimeter'].join(row) +"\n"


