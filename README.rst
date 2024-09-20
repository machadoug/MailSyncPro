MailSyncPro
===========

**MailSyncPro** is a robust command-line tool built on top of the **ImapCopy** repository, designed specifically for advanced users who need to transfer and synchronize email accounts between different IMAP servers. While retaining the core capabilities of ImapCopy, **MailSyncPro** introduces significant improvements that make the migration process more efficient, accurate, and easier to monitor.

Key Enhancements:
--------

*   **Email Duplication Check**: Before transferring messages, **MailSyncPro** checks whether an email already exists in the destination, preventing unnecessary duplication and reducing the risk of errors during migration.
    
*   **Folder Name Handling**: Folders with spaces in their names, which often cause errors in other tools, are seamlessly handled by MailSyncPro, ensuring smooth migration without manual folder name adjustments.
    
*   **Selective Folder Transfer**: Instead of skipping a specific number of messages when importing all emails, MailSyncPro allows you to skip entire folders, giving you granular control over what data gets transferred.
    
*   **Detailed Progress Information**: MailSyncPro provides real-time feedback by displaying the total number of messages in each source folder and how many have been successfully imported into the destination folder. This transparency ensures users are always informed of the migration status.
    
*   **\--test Mode**: The powerful `--test` option allows users to preview the migration process. It shows the number of emails in each folder and verifies whether the source and destination folders have matching email counts, making it easy to confirm that your migration will be successful before making any changes.
    

With these enhancements, **MailSyncPro** is ideal for system administrators, email service providers, or advanced users who need more control and visibility during email migration. Although it’s a command-line tool and not highly user-friendly for beginners, its features are designed to streamline complex migrations and ensure data integrity across IMAP servers.

Examples
--------

Assume you have, for example, a Gmail account and want to copy its folders to ``otherserver``.
You can use the IMAP protocol on both servers, **provided IMAP access is enabled on Gmail**.
Generally, you can copy folders and their contents between any two IMAP-enabled email servers.

Testing the connection and credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before actually copying messages, test the IMAP connection and credentials to both the source
server and your ``otherserver``; if the connection succeeds, IMAP folder names found on both servers
will be listed:

::

    python3 imapcopy.py \
      --test \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password"

Copying messages from folders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
To copy all the messages from, say, the ``INBOX`` folder of Gmail to the ``Inbox`` folder
of your ``otherserver``:

::

    python3 imapcopy.py \
      --verbose \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password" \
      "INBOX" "Inbox"

You can provide many folders to copy; alternating between source and destination.
For example, to copy from ``INBOX`` to ``Inbox`` and from ``[Gmail]/Sent Mail``
to ``Sent``:

::

    python3 imapcopy.py \
      --verbose \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password" \
      "INBOX"              "Inbox" \
      "[Gmail]/Sent Mail"  "Sent"

Copying a range of messages from a folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since Gmail throttles uploading and downloading email messages over IMAP, you 
may find the ``--skip`` and ``--limit`` options handy. For instance, If Gmail
disconnects you after copying 123 email messages out of your total 1000
messages in the example shown above, you may use the following command to
resume copying skipping the first 123 messages:

::

    python3 imapcopy.py \
      –-skip 123 \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password" \
      "INBOX" "Inbox"

Similarly, the ``--limit`` option allows you to copy only at most ``N`` messages
excluding the skipped messages. For example, the following command will copy
messages number 124 through 223 from Gmail:

::

    python3 imapcopy.py \
       --skip 123 --limit 100 \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password" \
      "INBOX" "Inbox"

Copying all folders and sub-folders from a server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--recurse`` option copies the contents of a folder and its sub-folders. Do not inform the folders to import all folders.
Also, if you use an empty string ``""`` as the source ``folder``, all the folders in
the source server  will be copied to the destination.

:: 

    python3 imapcopy.py \
      --recurse \
      "imap.googlemail.com:993"     "username@gmail.com:password" \
      "imap.otherserver.com.au:993" "username:password" \
      ""   "Imported"

Usage
-----

::
   
    usage: imapcopy.py [-h] [-t] [-c] [-r] [-q] [-v] [-s N] [-l N] source source-auth destination destination-auth [folders ...]

    positional arguments:
    source                source host, e.g. imap.googlemail.com:993
    source-auth           source host credentials, e.g. username@host.de:password
    destination           destination host, e.g. imap.otherhoster.com:993
    destination-auth      destination host credentials, e.g. username@host.de:password
    folders               list of folders, alternating between source folder and destination folder

    optional arguments:
    -h, --help            show this help message and exit
    -t, --test            do not copy, only test connections to source and destination
    -c, --create-folders  create folders on destination
    --skip-folders S      skip folders. Add multiple folders. e.g. "folder1" "Folder 2"       
    -r, --recurse         recurse into sub-folders
    -q, --quiet           be quiet, print no output
    -v, --verbose         print debug-level output
    -s N, --skip N        skip the first N message(s)
    -l N, --limit N       only copy at most N message(s)

Troubleshooting
-----

Emails don't show up on cPanel
~~~~~~~~~~~~~~~~~~~~
cPanel has a script to regenerate the dovecot files, however it will need to be run as the "root" user via SSH.
Below is cPanels guide on how to run the script
https://docs.cpanel.net/whm/scripts/the-remove_dovecot_index_files-script/
