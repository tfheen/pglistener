
CREATE OR REPLACE FUNCTION notify() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
EXECUTE 'NOTIFY ' || quote_ident(tg_relname);
EXECUTE 'NOTIFY update';
DELETE FROM last_updated;
INSERT INTO last_updated DEFAULT VALUES;
RETURN NULL;
END;
$$;

CREATE FUNCTION commas_sfunc(a text, b text) RETURNS text
    AS $$
begin
    if a = '' then
        return b;
    else
        return a || ',' || b;
    end if;
end;
$$
    LANGUAGE plpgsql;

CREATE AGGREGATE commas(text) (
    SFUNC = commas_sfunc,
    STYPE = text,
    INITCOND = ''
);

CREATE FUNCTION hostname(ip inet) RETURNS character varying
    LANGUAGE plperlu
    AS $_$
@_[0] =~ /(\d+)[.](\d+)[.](\d+)[.](\d+)/;
my $ip = pack 'W4', $1, $2, $3, $4;
my $name = gethostbyaddr($ip, 2);
return $name;
$_$;


CREATE TABLE account (
    account_id serial PRIMARY KEY,
    username varchar(20) NOT NULL,
    name varchar NOT NULL,
    shell varchar DEFAULT '/bin/bash'::varchar NOT NULL,
    password varchar,
    enabled boolean DEFAULT false NOT NULL,
    gpg_key varchar,
    email varchar,
    CONSTRAINT account_id_check CHECK ((account_id >= 1000))
);

CREATE TABLE phone (
    account_id integer REFERENCES account(account_id),
    phone_no varchar(30),
    phone_type varchar(30)       
);

CREATE TABLE grp (
    grp_id serial PRIMARY KEY,
    name varchar(20) NOT NULL,
    CONSTRAINT grp_id_check CHECK ((grp_id >= 100))
);

CREATE TABLE account_grp (
    account_id integer REFERENCES account(account_id),
    grp_id integer REFERENCES grp(grp_id)
);

CREATE VIEW apache AS
    SELECT account.username, account.password FROM account JOIN account_grp USING (account_id) JOIN grp USING (grp_id) WHERE (grp.name = 'varnish'::text) AND (account.password IS NOT NULL) AND (account.enabled = true);

CREATE TABLE last_updated (
    last_updated timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
);

CREATE TABLE ssh_key (
    ssh_key_id serial PRIMARY KEY,
    account_id integer NOT NULL,
    key_base64 text NOT NULL,
    comment text NOT NULL,
    hostname character varying
);

CREATE VIEW ssh_authorized_keys AS
    SELECT account.username, 'ssh-rsa'::character varying AS keytype, ssh_key.key_base64, ssh_key.comment FROM (ssh_key JOIN account USING (account_id)) WHERE ((account.enabled = true) AND ((ssh_key.hostname IS NULL) OR ((ssh_key.hostname)::text = ((SELECT hostname(pg_stat_activity.client_addr) AS hostname FROM pg_stat_activity WHERE (pg_stat_activity.procpid = pg_backend_pid())))::text)));


CREATE RULE notify_delete AS ON DELETE TO account DO NOTIFY update;
CREATE RULE notify_delete AS ON DELETE TO phone DO NOTIFY update;
CREATE RULE notify_delete AS ON DELETE TO account_grp DO NOTIFY update;
CREATE RULE notify_delete AS ON DELETE TO grp DO NOTIFY update;
CREATE RULE notify_delete AS ON DELETE TO ssh_key DO NOTIFY update;

CREATE RULE notify_insert AS ON INSERT TO account DO NOTIFY update;
CREATE RULE notify_insert AS ON INSERT TO phone DO NOTIFY update;
CREATE RULE notify_insert AS ON INSERT TO account_grp DO NOTIFY update;
CREATE RULE notify_insert AS ON INSERT TO grp DO NOTIFY update;
CREATE RULE notify_insert AS ON INSERT TO ssh_key DO NOTIFY update;

CREATE RULE notify_update AS ON UPDATE TO account DO NOTIFY update;
CREATE RULE notify_update AS ON UPDATE TO phone DO NOTIFY update;
CREATE RULE notify_update AS ON UPDATE TO account_grp DO NOTIFY update;
CREATE RULE notify_update AS ON UPDATE TO grp DO NOTIFY update;
CREATE RULE notify_update AS ON UPDATE TO ssh_key DO NOTIFY update;

