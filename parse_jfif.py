#!/usr/bin/python3

import argparse
import sys
import struct
from os import path

parser = argparse.ArgumentParser()
parser.add_argument("file")


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

def read_tag(fp):
    loc = fp.tell()
    if fp.read(1) != b'\xff':
        raise Exception("expected 0xff")

    tag = struct.unpack("B", fp.read(1))[0]
    if tag == 0xda or tag == 0xd9:
        return {
            "tag": tag,
            "len": 2,
            "loc": loc
        }

    len = struct.unpack('>H', fp.read(2))[0]
    return {
        "tag": tag,
        "len": len,
        "loc": loc
    }

def read_jfif(fp):
    # look for magic
    if fp.read(2) != b'\xff\xd8':
        raise Exception("invalid magic value")

    while True:        
        tag = read_tag(fp)
        if tag["tag"] == 0xda:
            break
        len = tag["len"]
        if len < 2:
            raise Exception("invalid length for tag")
        len -= 2
        data = fp.read(len)
        print("loc: %d,\ttag: %x, len: %d,\tname: %s" % (tag["loc"], tag["tag"], tag["len"], get_jpeg_tag_name(tag["tag"])))
        #if len < 256:
        #    print(data)
        #print("")

if __name__ == "__main__":
    params = parser.parse_args()
    if not path.isfile(params.file):
        print(f"Error: Can not open {params.file} for parsing.")    
        sys.exit(1)
    
    with open(params.file, "rb") as fp:
        read_jfif(fp)

