package Pglistener::Schema::Result::SSHKey;
use base qw/DBIx::Class::Core/;

__PACKAGE__->table('ssh_key');
__PACKAGE__->add_columns(qw/ ssh_key_id account_id key_base64 comment hostname /);
__PACKAGE__->set_primary_key('ssh_key_id');
__PACKAGE__->belongs_to(account => 'Pglistener::Schema::Result::Account', "account_id");

1;
