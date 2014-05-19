package Pglistener::Schema::Result::Account;
use base qw/DBIx::Class::Core/;

__PACKAGE__->table('account');
__PACKAGE__->add_columns(qw/ account_id username name shell password enabled gpg_key email/);
__PACKAGE__->set_primary_key('account_id');
__PACKAGE__->has_many(sshkeys => 'Pglistener::Schema::Result::SSHKey', "account_id" );
__PACKAGE__->has_many(account_grp => 'Pglistener::Schema::Result::AccountGrp', "account_id" );
__PACKAGE__->many_to_many(groups => 'account_grp', 'grp');

1;
