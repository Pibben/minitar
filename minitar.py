import click
import glob
import os
import itertools


@click.group()
def cli():
    pass


@cli.command('c', short_help='create')
@click.argument('dst', nargs=1)
@click.argument('src', nargs=-1)
@click.option('-k', '--key', default="00")
def create(dst, src, key):
    encode = lambda x: bytes(a ^ b for a, b in zip(itertools.cycle(bytes.fromhex(key)), x))
    files = []
    for s in src:
        if not os.path.exists(s):
            print(f"{s} does not exist")
            continue
        prefixLen = len(os.path.dirname(s)) + 1
        files.extend(glob.glob(s+"/**", recursive=True))

    with open(dst, 'wb') as outfile:
        outfile.write(encode("MINITAR\0".encode('utf-8')))
        files = [file.replace("\\", "/") for file in files if os.path.isfile(file)]
        numFiles = len(files)
        outfile.write(encode(numFiles.to_bytes(4, byteorder='big', signed=False)))

        offset = 0
        for file in files:
            path = file[prefixLen:]
            size = os.path.getsize(file)
            encpath = path.encode('utf-8')
            outfile.write(encode(len(encpath).to_bytes(1, byteorder='big', signed=False)))
            outfile.write(encode(encpath))
            outfile.write(encode(offset.to_bytes(4, byteorder='big', signed=False)))
            outfile.write(encode(size.to_bytes(4, byteorder='big', signed=False)))
            offset += size

        for file in files:
            with open(file, 'rb') as infile:
                outfile.write(encode(infile.read()))


@cli.command('x', short_help='extract')
@click.argument('src', nargs=1)
@click.option('-k', '--key', default="00")
def extract(src, key):
    decode = lambda x: bytes(a ^ b for a, b in zip(itertools.cycle(bytes.fromhex(key)), x))
    with open(src, 'rb') as infile:
        if decode(infile.read(8)).decode('utf-8') == "MINITAR\0":
            print("MAGIC OK")

        numFiles = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)

        infos = []
        for x in range(numFiles):
            info = {}
            pathSize = int.from_bytes(decode(infile.read(1)), byteorder='big', signed=False)
            info['path'] = decode(infile.read(pathSize)).decode('utf-8')
            offset = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)
            info['size'] = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)
            infos.append(info)

        for info in infos:
            print(f"Extracting {info['path']}...", end='')
            os.makedirs(os.path.dirname(info['path']), exist_ok=True)
            with open(info['path'], 'wb') as outfile:
                outfile.write(decode(infile.read(info['size'])))
            print(" OK.")


@cli.command('t', short_help='list')
@click.argument('src', nargs=1)
@click.option('-k', '--key', default="00")
def list(src, key):
    decode = lambda x: bytes(a ^ b for a, b in zip(itertools.cycle(bytes.fromhex(key)), x))
    with open(src, 'rb') as infile:
        if decode(infile.read(8)).decode('utf-8') == "MINITAR\0":
            print("MAGIC OK")

        numFiles = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)
        for x in range(numFiles):
            pathSize = int.from_bytes(decode(infile.read(1)), byteorder='big', signed=False)
            path = decode(infile.read(pathSize)).decode('utf-8')
            offset = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)
            size = int.from_bytes(decode(infile.read(4)), byteorder='big', signed=False)
            print(f"{path}: {size} @ {offset}")


if __name__ == '__main__':
    cli()
