from pglistener import PgListener

class ApacheVHostListener(PgListener):
  def __init__(self,cursor):
    PgListener.__init__(self)

    self.notifications=["asdf", "fdsa"]
    self.query="select webdomainname,homedir from vhost_hosts"
    self.format="%s %s\n"
    self.destination="vhost.test"
    self.cursor=cursor
    self.name="apachevhost"
    self.posthooks=["echo %s" % self.destination]
