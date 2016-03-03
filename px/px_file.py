import subprocess

import os


class PxFile(object):
    pass


def call_lsof():
    """
    Call lsof and return the result as one big string
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    # See OUTPUT FOR OTHER PROGRAMS: http://linux.die.net/man/8/lsof
    # Output lines can be in one of two formats:
    # 1. "pPID@" (with @ meaning NUL)
    # 2. "fFD@aACCESSMODE@tTYPE@nNAME@"
    lsof = subprocess.Popen(["lsof", '-F', 'fnapt0'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    return lsof.communicate()[0]


def lsof_to_files(lsof):
    pid = None
    file = None
    files = []
    for shard in lsof.split('\0'):
        if shard[0] == "\n":
            # Some shards start with newlines. Looks pretty when viewing the
            # lsof output in less, but makes the parsing code have to deal with
            # it.
            shard = shard[1:]

        if len(shard) == 0:
            # The output ends with a single newline, which we just stripped away
            break

        type = shard[0]
        value = shard[1:]

        if type == 'p':
            pid = int(value)
        elif type == 'f':
            if file:
                if file.type is not None and file.type != "REG":
                    # Decorate non-regular files with their type
                    file.name = "[" + file.type + "] " + file.name

            file = PxFile()
            file.fd = value
            file.pid = pid
            file.type = None
            files.append(file)
        elif type == 'a':
            file.access = {
                ' ': None,
                'r': "r",
                'w': "w",
                'u': "rw"}[value]
        elif type == 't':
            file.type = value
        elif type == 'n':
            file.name = value
        else:
            raise Exception("Unhandled type <{}> for shard <{}>".format(type, shard))

    return files


def get_all():
    return lsof_to_files(call_lsof())
