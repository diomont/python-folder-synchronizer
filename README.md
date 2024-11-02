# Python Folder Synchronizer

A python-based command-line program that periodically replicates the contents of an input folder into an output folder while running.
Requires Python version >= 3.7 to run. Uses no external modules.

Usage: `synchronize.py [-h] -i IN_PATH -o OUT_PATH -l LOG_PATH -p INTERVAL`

Any files present in the output folder that do not match the contents of the input folder will be deleted.

## Implementation Strategy

The main program loop uses the `asyncio` module to run the synchronization process periodically.
Folder structure and files are obtained by walking through the folders recursively, and files are compared by calculating their `blake2b` hashes.

Hashing and copying operations are performed concurrently to improve peformance on large amounts of files of considerable size, using the `concurrent.futures` module.

## Performance Considerations

Performance takes a hit when handling files of considerable size. Synchronizing a very large sile is slower than multiple smaller ones.

New synchronizations will not run if a previous one is still ongoing.

## Known Issues

Quitting the program may cause unintended stack traces in the console if done during one of the hashing or copying operations.

## Possible Improvements

Comparing the time of a file's last modification may be used to prevent unnecessary re-calculations of its hash, improving performance.
