from nssdb import NssDb

class NssPasswdDb(NssDb):
  def __init__(self,options):
    options['format'] = "%s:%s:%d:%d:%s:%s:%s"
    options['db-keys'] = { 0:".%s", 2:"=%d" }
    NssDb.__init__(self,options)
