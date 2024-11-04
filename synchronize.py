import os
import argparse
import logging
import asyncio
import concurrent.futures
from hashlib import blake2b
from shutil import copy2
from itertools import repeat


BLOCK_SIZE = 2**16
MAX_WORKERS = 20
MINIMUM_INTERVAL = 5


# Configure logging
logger = logging.getLogger("FileSync")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s | %(asctime)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def validate_args(args):
    if not os.path.isdir(args.input):
        print("Input path is not an existing directory")
        quit(1)
    if not os.path.isdir(args.output):
        print("Output path is not an existing directory")
        quit(1)
    if args.period < MINIMUM_INTERVAL:
        print("Synchronization interval must be at least {MINIMUM_INTERVAL} seconds")
        quit(1)
    if os.path.samefile(args.input, args.output):
        print("Input folder and output folder cannot be the same")
        quit(1)


def hash_file(path):
    # This method of hashing was used instead of `file_digest`, 
    # for compatibility with earlier versions of python
    hash = blake2b()
    try:
        with open(path, "rb") as f:
            while True:
                buffer = f.read(BLOCK_SIZE)
                if not buffer:
                    break
                hash.update(buffer)
        return hash.digest()
    except PermissionError:
        logger.warning("Could not read file '%s' due to missing permissions", path)
    except FileNotFoundError:
        logger.warning("File '%s' was moved, deleted or renamed during synchronization", path)


# Obtains file and directory paths recursively,
# storing the results in the given `files` and `dirs` lists.
# `rel_path` is the path to the file or directory with the initial `path` excluded.
# Each file has its `path` and `rel_path` stored as a tuple.
def walk_directory(path, files: list, dirs: list, rel_path=""):
    with os.scandir(path) as it:
        for entry in it:
            try:
                new_rel_path = os.path.join(rel_path, entry.name)
                if entry.is_dir():
                    dirs.append(new_rel_path)
                    walk_directory(entry.path, files, dirs, new_rel_path)
                elif entry.is_file():
                    files.append((new_rel_path, entry.path))
            except PermissionError:
                logger.warning("Could not read '%s' due to missing permissions", entry.path)
            except FileNotFoundError:
                logger.warning("File '%s' was moved, deleted or renamed during synchronization", entry.path)


def copy_file(source, destination, path):
    from_path = os.path.join(source, path)
    to_path = os.path.join(destination, path)
    try:
        copy2(from_path, to_path)
        logger.info("Copied file '%s' to '%s'", from_path, to_path)
    except PermissionError:
        logger.warning(
            "Could not copy file '%s' to '%s' due to missing permissions", 
            from_path, to_path)
    except FileNotFoundError:
        logger.warning("File '%s' was moved, deleted or renamed during synchronization", from_path)


def synchronize(source, replica):
    try:
        # Get input folder hashes and directories
        input_files = []
        input_dirs = []
        walk_directory(source, input_files, input_dirs)

        # Get output folder hashes and directories
        output_files = []
        output_dirs = []
        walk_directory(replica, output_files, output_dirs)

        input_hashes = dict()
        output_hashes = dict()
        hash_keys = (
            [ (input_hashes, rel_path) for rel_path, _ in input_files ]
            + [ (output_hashes, rel_path) for rel_path, _ in output_files ]
        )
        hash_paths = [ path for _, path in input_files ] + [ path for _, path in output_files ]

        # Calculate hashes concurrently
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
            for idx, digest in enumerate(ex.map(hash_file, hash_paths)):
                dic, key = hash_keys[idx]
                dic[key] = digest

        # The directory lists are ordered such that top-most folders always appear before
        # any folders contained in them (e.g. "folder1/folder2" will never appear before "folder1").
        # Because of this, iterating the list allows folder hierarchies to be created without issue.

        # Copy directories from input to output
        for path in input_dirs:
            full_path = os.path.join(replica, path)
            if not os.path.isdir(full_path):
                try:
                    os.mkdir(full_path)
                    logger.info("Created directory '%s'", full_path)
                except PermissionError:
                    logger.warning("Could not create directory '%s' due to missing permissions", 
                                full_path)
        
        # Delete files in output that are not present in input
        for path in output_hashes.keys():
            if path not in input_hashes:
                full_path = os.path.join(replica, path)
                try:
                    os.remove(full_path)
                    logger.info("Deleted file '%s'", full_path)
                except PermissionError:
                    logger.warning("Could not delete file '%s' due to missing permissions", 
                                full_path)
                except FileNotFoundError:
                    logger.warning("File '%s' was moved, deleted or renamed during deletion", 
                                full_path)

        # Delete directories in output that are not present in input.
        # Iterating the list in reverse guarantees that innermost folders are deleted before their parents.
        for path in reversed(output_dirs):
            if path not in input_dirs:
                full_path = os.path.join(replica, path)
                try:
                    os.rmdir(full_path)
                    logger.info("Deleted directory '%s'", full_path)
                except PermissionError:
                    logger.warning("Could not delete directory '%s' due to missing permissions", 
                                full_path)
                except FileNotFoundError:
                    logger.warning("Directory '%s' was moved, deleted or renamed during synchronization", 
                                full_path)

        # Check which files need to be copied from input to output
        to_copy = []
        for path, hash in input_hashes.items():
            # Copy file if it does not exist in output, or has a different hash
            if output_hashes.get(path, None) != hash:
                to_copy.append(path)
        
        # Copy files concurrently
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
            ex.map(copy_file, repeat(source, len(to_copy)), 
                   repeat(replica, len(to_copy)), to_copy)
    except KeyboardInterrupt:
        print("Exiting...")
        raise KeyboardInterrupt


# async wrapper for synchronize function
async def synchronize_wrapper(*args, **kwargs):
    synchronize(*args, **kwargs)


async def main():
    parser = argparse.ArgumentParser(description=
        """
        Performs one-way synchronization of the contents of two folders periodically. 
        Contents of the input folder are replicated to the output folder. 
        Any files in the output folder that are not present in the input folder will be deleted.
        """
    )
    parser.add_argument(
        "-i", "--input", 
        help="input folder path", 
        metavar="IN_PATH", required=True)
    parser.add_argument(
        "-o", "--output", 
        help="output folder path", 
        metavar="OUT_PATH", required=True)
    parser.add_argument(
        "-l", "--log", 
        help="log file path", 
        metavar="LOG_PATH", required=True)
    parser.add_argument(
        "-p", "--period", 
        help="synchronization interval in seconds", 
        type=int, metavar="INTERVAL", required=True)

    args = parser.parse_args()
    validate_args(args)

    file_handler = logging.FileHandler(args.log)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # perform initial synchronization
    task = asyncio.create_task(synchronize_wrapper(args.input, args.output))

    try:
        # synchronize periodically
        while True:
            await asyncio.sleep(args.period)
            # Only synchronize again if previous sync has already completed
            if task.done():
                task = asyncio.create_task(synchronize_wrapper(args.input, args.output))
            else:
                logger.warning("""
                                Syncronization was skipped because previous attempt was still running.
                                Consider using a larger interval""")
    except KeyboardInterrupt:
        task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
