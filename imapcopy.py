# -*- coding: utf-8 -*-
"""
    imapcopy

    Simple tool to copy folders from one IMAP server to another server.


    :copyright: (c) 2013 by Christoph Heer.
    :license: BSD, see LICENSE for more details.
"""

import sys
import hashlib
import imaplib
import logging
import argparse
import email 

# Define ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

class IMAP_Copy(object):
    source = {
        'host': 'localhost',
        'port': 993
    }
    source_auth = ()
    destination = {
        'host': 'localhost',
        'port': 993
    }
    destination_auth = ()
    folder_mapping = []

    def __init__(self, source_server, destination_server, folder_mapping,
                 source_auth=(), destination_auth=(), create_folders=False,
                 recurse=False, skip=0, limit=0, skip_folders=None):

        self.logger = logging.getLogger("IMAP_Copy")

        self.source.update(source_server)
        self.destination.update(destination_server)
        self.source_auth = source_auth
        self.destination_auth = destination_auth

        self.folder_mapping = folder_mapping
        self.create_folders = create_folders

        self.skip = skip
        self.limit = limit

        self.total_processed = 0  # Counter for total messages processed
        self.total_copied = 0  # Counter for total messages copied
        # List of folders to skip
        self.skip_folders = skip_folders if skip_folders is not None else []

        self.recurse = recurse

        
    def _connect(self, target):
        data = getattr(self, target)
        auth = getattr(self, target + "_auth")

        self.logger.info("Connect to %s (%s)" % (target, data['host']))
        if data['port'] == 993:
            connection = imaplib.IMAP4_SSL(data['host'], data['port'])
        else:
            connection = imaplib.IMAP4(data['host'], data['port'])

        if len(auth) > 0:
            self.logger.info("Authenticate at %s" % target)
            connection.login(*auth)

        setattr(self, '_conn_%s' % target, connection)
        self.logger.info("%s connection established" % target)
        # Detecting delimiter on destination server
        code, folder_list = connection.list()

        folder_name_list = []
        email_counts = []
        
        for box in folder_list:
            parts = box.decode('utf-8').split('"')
            if len(parts) == 5:
                folder_name_list.append(parts[3].strip())
            elif len(parts) == 3:
                folder_name_list.append(parts[2].strip())
            else:
                continue


        folder_names = ', '.join(folder_name_list)
        # self.logger.info("%s has the following folders: %s" % (target, folder_names))

        self.delimiter = folder_list[0].split(b'"')[1]

        return connection, folder_name_list


    def connect(self, test=False):
        src_mail, src_folders = self._connect('source')
        dest_mail, dest_folders = self._connect('destination')
        # src_folders and dest_folders are lists (array) of folder names

        # Check if the source and destination servers have the same number of folders
        
        print(f"{CYAN}Source folders:{RESET}", src_folders)  # Debugging print statement
        print(f"{CYAN}Destination folders:{RESET}", dest_folders)  # Debugging print statement
        
        src_set = set(src_folders)
        dest_set = set(dest_folders)

        # Sort the folders
        src_folders.sort()

        if test:
            # Check if the source folders and destination folders have the same number of emails
            for folder in src_folders:
                if folder in dest_folders:
                    # Properly quote the folder name
                    quoted_folder = f'"{folder}"'
                    src_status, _ = src_mail.select(quoted_folder)
                    dest_status, _ = dest_mail.select(quoted_folder)
                    
                    if src_status == 'OK' and dest_status == 'OK':
                        src_status, src_data = src_mail.search(None, 'ALL')
                        dest_status, dest_data = dest_mail.search(None, 'ALL')
                        
                        if src_status == 'OK' and dest_status == 'OK':
                            src_email_count = len(src_data[0].split())
                            dest_email_count = len(dest_data[0].split())
                            
                            if src_email_count != dest_email_count:
                                print(f"{YELLOW}Folder '{folder}' has different number of emails:{RESET}")
                                print(f"{RED}Source:{RESET} {src_email_count} emails")
                                print(f"{RED}Destination:{RESET} {dest_email_count} emails")
                            else:
                                print(f"{GREEN}Folder '{folder}' has the same number of emails in both source and destination:{RESET} {src_email_count} emails")
                        else:
                            print(f"{RED}Error searching emails in folder '{folder}'{RESET}")
                    else:
                        print(f"{RED}Error selecting folder '{folder}'{RESET}")


        # Output the number of folders in the source and destination
        # print(f"{CYAN}Number of folders in source:{RESET}", len(src_folders))  # Debugging print statement
        # print(f"{CYAN}Number of folders in destination:{RESET}", len(dest_folders))  # Debugging print statement
        
        only_in_src = src_set - dest_set
        only_in_dest = dest_set - src_set
        
        if only_in_src:
            print(f"{RED}Folders only in source:{RESET}")
            for folder in only_in_src:
                # self.logger.info('"%s" "%s"' % (folder, folder))
                print(f'{GREEN}"{folder}" "{folder}"{RESET}')  # Added print statement for debugging
        
        if only_in_dest:
            print(f"{RED}Folders only in destination:{RESET}")
            for folder in only_in_dest:
                # self.logger.info('"%s" "%s"' % (folder, folder))
                print(f'{GREEN}"{folder}" "{folder}"{RESET}')  # Added print statement for debugging



    def _disconnect(self, target):
        if not hasattr(self, '_conn_%s' % target):
            return

        connection = getattr(self, '_conn_%s' % target)
        if connection.state == 'SELECTED':
            connection.close()
            self.logger.info("Close folder on %s" % target)

        self.logger.info("Disconnect from %s server" % target)
        connection.logout()
        delattr(self, '_conn_%s' % target)

    def disconnect(self):
        self._disconnect('source')
        self._disconnect('destination')

    def copy(self, source_folder, destination_folder, skip, limit, recurse=True):

        # Skip the folder if it's in the skip_folders list
        if source_folder in self.skip_folders:
            self.logger.info("Skipping folder %s" % source_folder)
            return
            
        # There should be no files stored in / so we are bailing out
        if source_folder == '':
            return

        # Connect to source and open folder
        status, data = self._conn_source.select(source_folder, True)
        if status != "OK":
            self.logger.error("Couldn't open source folder %s" % source_folder)
            sys.exit(2)

        # Connect to destination and open or create folder
        status, data = self._conn_destination.select(destination_folder)
        if status != "OK" and not self.create_folders:
            self.logger.error("Couldn't open destination folder %s" % destination_folder)
            sys.exit(2)
        elif status != "OK":
            self.logger.info("Create destination folder %s" % destination_folder)
            status, response = self._conn_destination.create(destination_folder)
            if status != "OK":
                if b'ALREADYEXISTS' in response:
                    self.logger.info("Destination folder %s already exists" % destination_folder)
                else:
                    self.logger.error("Failed to create destination folder %s: %s" % (destination_folder, response))
                    sys.exit(2)
            else:
                self.logger.info("Successfully created destination folder %s" % destination_folder)

            # Subscribe to the newly created folder
            status, response = self._conn_destination.subscribe(destination_folder)
            if status != "OK":
                self.logger.error("Failed to subscribe to destination folder %s: %s" % (destination_folder, response))
            else:
                self.logger.info("Successfully subscribed to destination folder %s" % destination_folder)

            status, data = self._conn_destination.select(destination_folder)
            if status != "OK":
                self.logger.error("Failed to select destination folder %s: %s" % (destination_folder, data))
                sys.exit(2)
            else:
                self.logger.info("Successfully selected destination folder %s" % destination_folder)

        # Look for mails
        self.logger.info("Looking for mail in %s" % source_folder)
        status, data = self._conn_source.search(None, 'ALL')
        data = data[0].split()
        mail_count = len(data)

        self.logger.info("Start copy %s => %s (%d mails)" % (source_folder, destination_folder, mail_count))

        progress_count = 0
        copy_count = 0

        for msg_num in data:
            progress_count += 1
            self.total_processed += 1  # Increment total processed counter
            if progress_count <= skip:
                self.logger.info("Skipping mail %d of %d" % (
                    progress_count, mail_count))
                continue
            else:
                status, data = self._conn_source.fetch(msg_num, '(RFC822 FLAGS INTERNALDATE)')

                message = data[0][1]
                msg = email.message_from_bytes(message)
                message_id = msg['Message-ID']

                 # Properly quote the Message-ID
                if not message_id:
                    self.logger.warning(f"{YELLOW}Message{RESET} {BOLD} {msg_num} {YELLOW} has no Message-ID. {RED} Copying without checking for duplicates {RESET}")
                    # Print
                    print(f"{YELLOW}Message{RESET} {BOLD} {msg_num} {YELLOW} has no Message-ID. {RED} Copying without checking for duplicates {RESET}")
                else:
                    # Escape double quotes and ensure the Message-ID is properly quoted
                    # Clean a string, remove all spaces and line breaks
                    message_id_cleaned = message_id.replace('  ', '').replace(' ', '').replace('\n', '').replace('\r', '').replace('\\', '\\\\').replace('"', '\\"')

                    self.logger.debug(f"Quoted Message-ID: {message_id_cleaned}")
                    # Print colored Message-ID
                    print(f"{CYAN}Message-ID:{RESET} {BOLD}{message_id}{RESET}")


                    # Check if the message already exists in the destination folder
                    status, dest_data = self._conn_destination.search(None, f'HEADER Message-ID "{message_id_cleaned}"')
                    if status == "OK" and dest_data[0]:
                        self.logger.info("Mail with Message-ID %s already exists in destination folder %s" % (message_id, destination_folder))  
                        continue

                flags_line = data[0][0].decode('ascii')
                if flags_line.find('FLAGS') < 0 and len(data) > 1:
                    flags_line = data[1].decode('ascii')

                flags_start = flags_line.index('FLAGS (') + len('FLAGS (')
                flags_end = flags_line.index(')', flags_start)

                flags = '(' + flags_line[flags_start:flags_end] + ')'

                 # Remove the \RECENT flag, the script was throwing errors when trying to copy the mail
                flags = flags.replace('\\Recent', '').replace('\\RECENT', '').strip()
                if flags == '()':
                    flags = None

                internaldate_start = flags_line.index('INTERNALDATE ') + len('INTERNALDATE ')
                internaldate_end = flags_line.find(' RFC822', internaldate_start)
                if internaldate_end < 0:
                    internaldate_end = flags_line.find(' FLAGS', internaldate_start)
                if internaldate_end < 0:
                    internaldate_end = flags_line.find(')', internaldate_start)
                if internaldate_end < 0:
                    internaldate_end = len(flags_line)

                internaldate = flags_line[internaldate_start:internaldate_end]

                self._conn_destination.append(
                    destination_folder, flags, internaldate, message,
                )

                copy_count += 1
                self.total_copied += 1  # Increment total copied counter
                message_sha1 = hashlib.sha1(message).hexdigest()

                self.logger.info("Copy mail %d of %d (copy_count=%d, sha1(message)=%s)" % (
                    progress_count, mail_count, copy_count, message_sha1))

                if limit > 0 and copy_count >= limit:
                    self.logger.info("Copy limit %d reached (copy_count=%d)" % (
                        limit, copy_count))
                    break

        self.logger.info("Copy complete %s => %s (%d out of %d messages copied)" % (
            source_folder, destination_folder, copy_count, mail_count))
        
        # Print total processed count
        self.logger.info("Total messages copied: %d; Total messages processed: %d" % (self.total_copied, self.total_processed))


        if self.recurse and recurse:
            self.logger.info("Getting list of folders under %s" % source_folder)
            connection = self._conn_source
            typ, data = connection.list(source_folder)

            # Sort the folders
            data.sort()

            for d in data:
                if d:
                    l_resp = d.decode('utf-8').split('"')
                    # response = '(\HasChildren) "/" INBOX'
                    if len(l_resp) == 3:

                        source_mbox = d.decode('utf-8').split('"')[2].strip()
                        # make sure we don't have a recursive loop
                        if source_mbox != source_folder:
                            # maybe better use regex to replace only start of the souce name
                            dest_mbox = source_mbox.replace(source_folder, destination_folder)
                            self.logger.info("starting copy of folder %s to %s " % (source_mbox, dest_mbox))
                            self.copy(source_mbox, dest_mbox, skip, limit, False)

    def run(self):
        # print self.folder_mapping for debugging
        try:
            self.connect()  

            for source_folder, destination_folder in self.folder_mapping:
                # print for debugging
                # print(f"{CYAN}Copying folder:{RESET} {source_folder} {CYAN}to:{RESET} {destination_folder}")

                if ' ' in source_folder and '"' not in source_folder:
                    # debbuging print statement
                    # print(f"{RED}Source folder has a space{RESET}")
                    source_folder = '"%s"' % source_folder
                if ' ' in destination_folder and '"' not in destination_folder:
                    # debbuging print statement
                    # print(f"{RED}Destination folder has a space{RESET}")
                    destination_folder = '"%s"' % destination_folder

                # print for debugging
                # print(f"{CYAN}Copying folder:{RESET} {source_folder} {CYAN}to:{RESET} {destination_folder}")
                self.copy(source_folder, destination_folder, self.skip, self.limit)
        finally:
            self.disconnect()

    def test_connections(self):
        self.logger.info("Testing connections to source and destination")
        try:
            self.connect(True)
            self.logger.info("Test OK")
        except Exception as e:
            self.logger.error("Connection error: %s" % str(e))
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source',
                        help="source host, e.g. imap.googlemail.com:993")

    parser.add_argument('source_auth', metavar='source-auth',
                        help="source host credentials, e.g. username@host.de:password")

    parser.add_argument('destination',
                        help="destination host, e.g. imap.otherhoster.com:993")

    parser.add_argument('destination_auth', metavar='destination-auth',
                        help="destination host credentials, e.g. username@host.de:password")

    parser.add_argument('folders', type=str, nargs='*',
                        help="list of folders, alternating between source folder and destination folder")

    parser.add_argument('-t', '--test', dest='test_connections',
                        action="store_true", default=False,
                        help="do not copy, only test connections to source and destination")

    parser.add_argument('-c', '--create-folders', dest='create_folders',
                        action="store_true", default=False,
                        help="create folders on destination")

    parser.add_argument('-r', '--recurse', dest='recurse',
                        action="store_true", default=False,
                        help="recurse into subfolders")

    parser.add_argument('-q', '--quiet', action="store_true", default=False,
                        help="be quiet, print no output")

    parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help="print debug-level output")

    def check_negative(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid positive integer value" % value)
        return ivalue

    parser.add_argument("-s", "--skip", default=0, metavar="N", type=check_negative,
                        help="skip the first N message(s)")

    # Add an argument to skip folders.
    # Usage: --skip-folders "folder1" "folder2" "folder3"
    parser.add_argument('--skip-folders', nargs='+', default=[], 
                        help="list of folders to skip during the copy process")

    parser.add_argument("-l", "--limit", default=0, metavar="N", type=check_negative,
                        help="only copy at most N message(s)")

    args = parser.parse_args()

    _source = args.source.split(':')
    source = {'host': _source[0]}
    if len(_source) > 1:
        source['port'] = int(_source[1])

    _destination = args.destination.split(':')
    destination = {'host': _destination[0]}
    if len(_destination) > 1:
        destination['port'] = int(_destination[1])

    source_auth = tuple(args.source_auth.split(':'))
    destination_auth = tuple(args.destination_auth.split(':'))

    if not args.test_connections:
        if len(args.folders) == 0:
            # If no specific folders are provided, copy all folders
            source_conn = imaplib.IMAP4_SSL(source['host'], source['port'])
            source_conn.login(*source_auth)
            status, folders = source_conn.list()
            if status != "OK":
                print("Failed to retrieve folders from source")
                sys.exit(1)
            args.folders = []
            for folder in folders:
                parts = folder.decode('utf-8').split('"')
                if len(parts) == 5:
                    args.folders.append(parts[3].strip())
                    args.folders.append(parts[3].strip())
                elif len(parts) == 3:
                    args.folders.append(parts[2].strip())
                    args.folders.append(parts[2].strip())
                else:
                    print(f"Skipping invalid folder entry: {folder.decode()}")

            source_conn.logout()
        elif len(args.folders) < 2:
            print("Missing folders")
            sys.exit(1)
        elif len(args.folders) % 2 != 0:
            print("Please provide an even number of folders")
            sys.exit(1)



    # Sort the folders before creating the folder_mapping
    args.folders.sort()


    folder_mapping = list(zip(args.folders[::2], args.folders[1::2]))

    # Debugging: Print sorted folder_mapping
    # print("Sorted folder_mapping:", folder_mapping)
    

    imap_copy = IMAP_Copy(source, destination, folder_mapping, source_auth,
                          destination_auth, create_folders=args.create_folders, skip_folders=args.skip_folders,
                          recurse=args.recurse, skip=args.skip, limit=args.limit)

    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    imap_copy.logger.addHandler(streamHandler)

    if not args.quiet:
        streamHandler.setLevel(logging.INFO)
        imap_copy.logger.setLevel(logging.INFO)
    if args.verbose:
        streamHandler.setLevel(logging.DEBUG)
        imap_copy.logger.setLevel(logging.DEBUG)

    try:
        if args.test_connections:
            imap_copy.test_connections()
        else:
            imap_copy.run()
    except KeyboardInterrupt:
        imap_copy.disconnect()


if __name__ == '__main__':
    main()
