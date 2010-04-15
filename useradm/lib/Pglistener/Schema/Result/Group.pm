package Pglistener::Schema::Result::Group;
use base qw/DBIx::Class::Core/;

__PACKAGE__->table('grp');
__PACKAGE__->add_columns(qw/grp_id name/);
__PACKAGE__->set_primary_key('grp_id');
__PACKAGE__->has_many(account_grp => 'Pglistener::Schema::Result::AccountGrp', "grp_id");
__PACKAGE__->many_to_many(members => 'account_grp', 'account');

1;
