package Pglistener::Schema::Result::Email;
use base qw/DBIx::Class::Core/;

__PACKAGE__->table('email');
__PACKAGE__->add_columns(qw/ localpart domainpart account_id customary email_id /);
#__PACKAGE__->set_primary_key('email_id');
__PACKAGE__->belongs_to(account => 'Pglistener::Schema::Result::Account', "account_id");

1;
