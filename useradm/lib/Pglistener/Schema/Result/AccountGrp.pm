package Pglistener::Schema::Result::AccountGrp;
use base qw/DBIx::Class::Core/;

__PACKAGE__->table('account_grp');
__PACKAGE__->add_columns(qw/ account_id grp_id /);
__PACKAGE__->set_primary_key('account_id', 'grp_id');
__PACKAGE__->belongs_to(account => 'Pglistener::Schema::Result::Account', "account_id");
__PACKAGE__->belongs_to(grp => 'Pglistener::Schema::Result::Group', "grp_id");

1;
