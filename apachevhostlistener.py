from pglistener import PgListener

class ApacheVHostListener(PgListener):
  def __init__(self,DSN):

    self.DSN=DSN
    PgListener.__init__(self,self.DSN)

    self.notifications=["asdf"]
    self.query="select webdomainname,homedir from vhost_hosts"
    self.format="%s %s\n"
    self.destination="vhost.test"
    self.name="apachevhost"
    self.posthooks=["echo %s" % self.destination]
