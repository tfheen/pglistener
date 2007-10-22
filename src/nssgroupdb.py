from nssdb import NssDb

class NssGroupDb(NssDb):
  def __init__(self,options):
    options['format'] = "%s:%s:%d:%s"
    options['db-keys'] = { 0:".%s", 2:"=%d" }
    NssDb.__init__(self,options)
