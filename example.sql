
CREATE FUNCTION notify() RETURNS trigger
    AS $$
begin
execute 'notify ' || quote_ident(tg_relname);
return null;
end;
$$
    LANGUAGE plpgsql;

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
