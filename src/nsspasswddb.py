from nssdb import NssDb

class NssPasswdDb(NssDb):
  def __init__(self,options):
    options['format'] = "%s:%s:%d:%d:%s:%s:%s"
    NssDb.__init__(self,options)
