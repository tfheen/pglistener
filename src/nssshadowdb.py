from nssdb import NssDb

class NssShadowDb(NssDb):
  def __init__(self,options):
    options['format'] = "%s:%s:13045:0:99999:7:::"
    options['db-keys'] = { 0:".%s" }
    NssDb.__init__(self,options)
