from pglistener import PgListener

class ApacheVhost(PgListener):
  def __init__(self,options):
    options['format']="%s\t%s/webs/%s\n"
    PgListener.__init__(self,options)



