from nssdb import NssDb

class NssGroupDb(NssDb):
  def __init__(self,options):
    options['format'] = "%s:%s:%d:%s"
    NssDb.__init__(self,options)
