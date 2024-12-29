#!/usr/bin/python3

import argparse
import sys
import struct
from os import path


def get_jpeg_tag_name(tag):
    # Define a dictionary mapping tag numbers (in hex) to their symbol names
    jpeg_tags = {
        0xD8: "SOI (Start of Image)",
        0xE0: "APP0 (JFIF tag)",
        0xCC: "DAC (Definition of Arithmetic Coding)",
        0xDB: "DQT (Definition of Quantization Tables)",
        0xDD: "DRI (Define Restart Interval)",
        0xE1: "APP1 (Exif Data)",
        0xEE: "APP14 (Often used for Copyright Entries)",
        0xFE: "COM (Comments)",
        0xDA: "SOS (Start of Scan)",
        0xD9: "EOI (End of Image)",
        0xC0: "SOF0 (Baseline DCT)",
        0xC1: "SOF1 (Extended Sequential DCT)",
        0xC2: "SOF2 (Progressive DCT)",
        0xC3: "SOF3 (Lossless, Sequential)",
        0xC4: "DHT (Huffman Table Definition)",
        0xC5: "SOF5 (Differential Sequential DCT)",
        0xC6: "SOF6 (Differential Progressive DCT)",
        0xC7: "SOF7 (Differential Lossless, Sequential)",
        0xC8: "JPG (Reserved for JPEG Extensions)",
        0xC9: "SOF9 (Extended Sequential DCT)",
        0xCA: "SOF10 (Progressive DCT)",
        0xCB: "SOF11 (Lossless, Sequential)",
        0xCD: "SOF13 (Differential Sequential DCT)",
        0xCE: "SOF14 (Differential Progressive DCT)",
        0xCF: "SOF15 (Differential Lossless, Sequential)",
    }
    # Return the corresponding symbol name or a message if not found
    return jpeg_tags.get(tag, "Unknown Tag")


def seek_next(fp):
    loc = fp.tell()
    if fp.read(1) != b'\xff':
        raise Exception('Expected 0xff')

    tag = struct.unpack('B', fp.read(1))[0]
    if tag == 0xda or tag == 0xd9:
        fp.seek(0, 2)
        len = fp.tell() - loc
        return { "loc": loc, "tag": tag, "len": len }

    len = struct.unpack('>H', fp.read(2))[0]
    fp.seek(len - 2, 1)
    return { "loc": loc, "tag": tag, "len": len + 2 }


def create_toc(fp):
    fp.seek(0)
    TOC = []
    if fp.read(2) != b'\xff\xd8':
        raise Exception("invalid magic value")

    while True:
        tag = seek_next(fp)
        TOC.append(tag)
        if tag["tag"] == 0xda:
            fp.seek(0)
            return TOC


def check_holokote(fp, entry):
    if entry["tag"] != 0xe0:
        return False
    pos = fp.tell()
    fp.seek(entry["loc"])
    try:
        if fp.read(1) != b'\xff':
            return False

        if fp.read(1) != b'\xe0':
            return False

        fp.read(2)
        if fp.read(15) != b'ULTRAIDHOLOKOTE':
            return False
        return True
    finally:
        fp.seek(pos)


def seek_entry(fp, entry):
    fp.seek(entry["loc"])


def read_entry(fp, entry):
    seek_entry(fp, entry)
    return fp.read(entry["len"])


def list_command(args):
    print(f"Reading {args.file}:")
    with open(args.file, "rb") as fp:
        TOC = create_toc(fp)
        for entry in TOC:
            print("\t%i:\t%x\t%d\t%s" % (entry["loc"], entry["tag"], entry["len"], get_jpeg_tag_name(entry["tag"])))


def patch_command(args):
    print(f"Patching file: {args.input} with patch: {args.patch}")
    with open(args.input, "rb") as fin:
        with open(args.output, "wb") as fout:
            TOC = create_toc(fin)

            # add magic first
            fout.write(b'\xff\xd8')
            for entry in TOC:
                if check_holokote(fin, entry):
                    # replace patch
                    print(f'replace section {fin.tell()} from patch')
                    with open(args.patch, "rb") as patch:
                        patch.seek(0, 2)
                        len = patch.tell()
                        patch.seek(0)
                        fout.write(fin.read(len))
                else:
                    # copy original data
                    print(f'write section {fin.tell()} to {fout.tell()}')
                    fout.write(read_entry(fin, entry))


def dump_command(args):
    print(f'Reading {args.input} and dump to {args.output}')
    with open(args.input, "rb") as fin:
        TOC = create_toc(fin)
        for entry in TOC:
            if not check_holokote(fin, entry):
                continue

            print(f'Writing {args.output}')
            with open(args.output, "wb") as fout:
                seek_entry(fin, entry)
                len = entry["len"]
                fout.write(fin.read(len))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
        
    subparsers = parser.add_subparsers(dest='command', help='Modules')

    list_parser = subparsers.add_parser('list', help='List all JFIF Headers')
    list_parser.add_argument('file', type=str, default='all', help='The file to list the sections from.')
    list_parser.set_defaults(func=list_command)

    patch_parser = subparsers.add_parser('patch', help='Patch APP0 section in file.')
    patch_parser.add_argument('input', type=str, help='File to read from.')
    patch_parser.add_argument('output', type=str, help='File to write to.')
    patch_parser.add_argument('patch', type=str, help='Patch to put into the APP0 section.')
    patch_parser.set_defaults(func=patch_command)

    dump_parser = subparsers.add_parser('dump', help='Dump APP0 section to file.')
    dump_parser.add_argument('input', type=str, default='all', help='JFIF input file.')
    dump_parser.add_argument('output', type=str, default='all', help='The output file to dump the section to.')
    dump_parser.set_defaults(func=dump_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

