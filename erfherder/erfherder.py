#!/usr/bin/env python
import argparse, os, sys, fnmatch, hashlib

from pynwn.file.erf import Erf

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', action='version', version='0.1')
subparsers = parser.add_subparsers(description='erfherder commands', dest='sub_commands')

# pack
parser_pack = subparsers.add_parser('pack', description='Pack files and directories into an ERF file.')
parser_pack.add_argument('--exclude', help='Exclude files, directories, patterns.', action='append')
parser_pack.add_argument('output', help='Output ERF. Extension determines ERF type.')
parser_pack.add_argument('input', help='Add files/directories to add.', nargs='+')

# dump
parser_pack = subparsers.add_parser('dump', description='Dump files from an ERF.')
parser_pack.add_argument('-p', '--pattern', help='Unix wildcard pattern.')
parser_pack.add_argument('input', help='Source ERF.')
parser_pack.add_argument('output', help='Output directory.')

# ls
parser_pack = subparsers.add_parser('ls', description='List files from an ERF.')
parser_pack.add_argument('input', help='Source ERF.')

# dupes
#parser_pack = subparsers.add_parser('dupes', description='Find duplicate files by sha1')
#parser_pack.add_argument('-p', '--pattern', help='Unix wildcard pattern.')
#parser_pack.add_argument('input', help='Input ERF files.', nargs='+')

def dump(source, dest, pat):
    if not os.path.isdir(dest):
        os.mkdir(dest)
    elif not os.path.isfile(source):
        print("Error: Unable to locate '%s'." % source, file=sys.stderr)
        return

    try:
        out = Erf.from_file(source)
        for co in out.content:
            if not pat or fnmatch.fnmatch(co.get_filename(), pat):
                co.write_to(os.path.join(dest, co.get_filename()))

    except ValueError as e:
        print("Error: Unable to open %s: %s." % str(e), file=sys.stderr)

def pack(fout, fin, excludes):
    def check_excluded(path):
        ignore = False
        if excludes:
            for ex in excludes:
                if fnmatch.fnmatch(path, ex):
                    print("Ignoring: " + path)
                    ignore = True

        return ignore

    def add_file(erf, file):
        if os.path.isfile(file):
            if check_excluded(file): return
            try:
                out.add_file(file)
            except ValueError as e:
                print("Skipping: " + str(e))
        else:
            print("Error: Unable to add: %s is not a file." % f, file=sys.stderr)

    ext = os.path.splitext(fout)[1][1:].upper()
    if not ext in Erf.TYPES:
        print("Error: Unsupported output file extension: %s." % ext, file=sys.stderr)
        return

    if os.path.isfile(fout):
        out = Erf.from_file(fout)
    else:
        out = Erf(ext)

    for f in fin:
        if os.path.isdir(f):
            for root, _, files in os.walk(f):
                if check_excluded(root): continue

                for file in files:
                    add_file(out, os.path.join(root, file))
        else:
            add_file(out, f)

    out.write_to(args.output)

def ls(erf):
    e = Erf.from_file(erf)
    res = []
    for co in e.content:
        res.append((co.get_filename(), co.size))

    res = sorted(res, key=lambda c: c[0])
    for r in res:
        print('%-20s %d' % r)


def dupes(erfs):
    shas = {}
    for erf in erfs:
        e = Erf.from_file(erf)
        for co in e.content:
            m = hashlib.sha1()
            m.update(co.get())
            d = m.hexdigest()
            t = (erf, co.get_filename())
            if d in shas:
                shas[d].append(t)
            else:
                shas[d] = [t]

    for k, v in shas.items():
        if len(v) > 1:
            print(v)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv.append('--help')

    args = parser.parse_args()
    if args.sub_commands == 'pack':
        pack(args.output, args.input, args.exclude)

    elif args.sub_commands == 'dump':
        dump(args.input, args.output, args.pattern)

    elif args.sub_commands == 'dupes':
        dupes(args.input)

    elif args.sub_commands == 'ls':
        ls(args.input)

    elif args.sub_commands == "help":
        if not args.command:
            args.parse_args(['--help'])
        else:
            args.parse_args([parsed.command, '--help'])
