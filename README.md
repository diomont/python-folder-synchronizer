# Python Folder Synchronizer

A python-based command-line program that periodically replicates the contents of an input folder into an output folder while running.
Requires Python version >= 3.8 to run. Uses no external modules other than `pytest`, which is not required to run the program, only the tests.

Usage: `synchronize.py [-h] -i IN_PATH -o OUT_PATH -l LOG_PATH -p INTERVAL`

Any files present in the output folder that do not match the contents of the input folder will be deleted.

## Implementation Strategy

The main program loop uses the `asyncio` module to run the synchronization process periodically.
Folder structure and files are obtained by walking through the folders recursively, and files are compared by calculating their `blake2b` hashes.

Hashing and copying operations are performed concurrently to improve peformance on large amounts of files of considerable size, using the `concurrent.futures` module.

## Testing

A number of tests were written for the synchronization function, which use temporary files and directories. They require `pytest` to run: `pip install pytest`.

To run the tests: `python -m pytest`

Note that these tests do not test the program while running on the command line, only the synchronization function itself.

## Performance Considerations

Performance takes a hit when handling files of considerable size. Synchronizing a very large sile is slower than multiple smaller ones.

The use of threading adds some overhead that makes synchronizing very small files slower than it would be without, but greatly improves speed when files are larger.

New synchronizations will not run if a previous one is still ongoing.

## Known Issues

Quitting the program may cause unintended stack traces in the console if done during one of the hashing or copying operations.

## Possible Improvements

Comparing the time of a file's last modification may be used to prevent unnecessary re-calculations of its hash, improving performance.
