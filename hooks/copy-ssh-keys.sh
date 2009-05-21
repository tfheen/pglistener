#!/bin/sh
#
# Copy SSH keys from one directory to another, while changing the owner to
# root and setting the mode to 600.

src="/var/lib/pglistener/sshkeys/"
dst="/var/lib/misc/sshkeys/"

# copy files from $src to $dst
(cd "$src";
    find -maxdepth 1 -type f \
        -exec install -m644 -oroot -groot '{}' "$dst" ';')

# remove files from $dst which aren't in $src
(cd "$dst";
    find -maxdepth 1 -type f \
        '(' -exec test ! -e "$src/{}" ';' \
            -exec rm '{}' ';' \
        ')')

