import pytest
import os
from pathlib import Path
from synchronize import synchronize


@pytest.fixture
def paths(tmp_path):
    in_ = tmp_path / "in"
    out = tmp_path / "out"
    in_.mkdir()
    out.mkdir()
    return [in_, out]


# Helper functions

# Returns True if file contents are the same
def compare_files(path1, path2) -> bool:
    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        return f1.read() == f2.read()

# Returns True if directory structures are the same
def compare_structure(path1, path2) -> bool:
    f1 = [ (dirnames, filenames) for _, dirnames, filenames in os.walk(path1) ]
    f2 = [ (dirnames, filenames) for _, dirnames, filenames in os.walk(path2) ]
    return all( t1 == t2 for t1, t2 in zip(f1,f2) )


# Setup for each test describes the contents of the input and output folders as follows:
#
# Input:
#   folder1/
#       file1:  content of file
#       folder2/
#   file2:  content of file
# Output:
#   fileA: content of file


def test_copy_file(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   file.txt:   "Sample content"
    # Output:
    #   [empty]
    f = in_ / "file.txt"
    f.write_text("Sample content")

    synchronize(in_, out)

    f2 = out / "file.txt"
    assert f2.exists()
    assert compare_files(f, f2)
    


def test_delete_file(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   [empty]
    # Output:
    #   file.txt:   "Sample content"
    f = out / "file.txt"
    f.write_text("Sample content")

    synchronize(in_, out)

    assert not f.exists()


def test_copy_directory(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   folder/
    # Output:
    #   [empty]
    d = in_ / "folder"
    d.mkdir()

    synchronize(in_, out)

    d2 = out / "folder"
    assert d2.exists() and d2.is_dir()


def test_delete_directory(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   [empty]
    # Output:
    #   folder/
    d = out / "folder"
    d.mkdir()

    synchronize(in_, out)

    assert not d.exists()


def test_alter_file_contents(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   file.txt:   "Different content"
    # Output:
    #   file.txt:   "Sample content"
    f = in_ / "file.txt"
    f.write_text("Different content")
    f2 = out / "file.txt"
    f2.write_text("Sample content")

    synchronize(in_, out)

    assert f2.exists()
    assert compare_files(f, f2)


def test_alter_file_name(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   diff_name.txt:   "Sample content"
    # Output:
    #   file.txt:   "Sample content"
    f = in_ / "diff_name.txt"
    f.write_text("Sample content")
    f2 = out / "file.txt"
    f2.write_text("Sample content")

    synchronize(in_, out)

    f3 = out / "diff_name.txt"
    assert not f2.exists()
    assert f3.exists()
    assert compare_files(f, f3)


def test_copy_dir_and_file(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   folder/
    #       file.txt:   "Sample content"
    # Output:
    #   [empty]
    d = in_ / "folder"
    d.mkdir()
    f = d / "file.txt"
    f.write_text("Sample content")

    synchronize(in_, out)

    f2 = out / "folder" / "file.txt"
    assert f2.exists()
    assert compare_files(f, f2)


def test_delete_dir_and_file(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   [empty]
    # Output:
    #   folder/
    #       file.txt:   "Sample content"
    d = out / "folder"
    d.mkdir()
    f = d / "file.txt"
    f.write_text("Sample content")

    synchronize(in_, out)

    assert not d.exists()
    assert not f.exists()


def test_copy_multiple_files(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   file.txt:   "Sample content"
    #   file2.txt:  "Another file"
    # Output:
    #   [empty]
    fi1 = in_ / "file.txt"
    fi1.write_text("Sample content")
    fi2 = in_ / "file2.txt"
    fi2.write_text("Another file")

    synchronize(in_, out)

    fo1 = out / "file.txt"
    fo2 = out / "file2.txt"
    assert fo1.exists()
    assert fo2.exists()
    assert compare_files(fi1, fo1)
    assert compare_files(fi2, fo2)


def test_delete_multiple_files(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   [empty]
    # Output:
    #   file.txt:   "Sample content"
    #   file2.txt:  "Another file"
    f1 = out / "file.txt"
    f1.write_text("Sample content")
    f2 = out / "file2.txt"
    f2.write_text("Another file")

    synchronize(in_, out)

    assert not f1.exists()
    assert not f2.exists()


def test_copy_subdirs(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   folder/
    #       subfolder1/
    #       subfolder2/
    #   folder2/
    #       subfolder/
    # Output:
    #   [empty]
    di1 = in_ / "folder"
    di1.mkdir()
    di1_1 = di1 / "subfolder1"
    di1_1.mkdir()
    di1_2 = di1 / "subfolder2"
    di1_2.mkdir()

    di2 = in_ / "folder2"
    di2.mkdir()
    di2_1 = di2 / "subfolder"
    di2_1.mkdir()

    synchronize(in_, out)

    do1_1 = out / "folder" / "subfolder1"
    do1_2 = out / "folder" / "subfolder2"
    do2_1 = out / "folder2" / "subfolder"
    assert do1_1.exists() and do1_1.is_dir()
    assert do1_2.exists() and do1_2.is_dir()
    assert do2_1.exists() and do2_1.is_dir()


def test_assortment(paths):
    in_: Path = paths[0]
    out: Path = paths[1]

    # Input:
    #   folder/
    #       subfolder1/
    #           subfile.txt:    "Subfile content"
    #       subfolder2/
    #   file.txt:   "Sample content"
    # Output:
    #   folder/
    #       subfolder1/
    #           subfile.txt:    "Different content"
    #   extrafolder/
    #   extrafile.txt:  "Extra file content"
    di1 = in_ / "folder"
    di1.mkdir()
    di1_1 = di1 / "subfolder1"
    di1_1.mkdir()
    di1_2 = di1 / "subfolder2"
    di1_2.mkdir()

    fi1 = di1_1 / "subfile.txt"
    fi1.write_text("Subfile content")
    fi2 = in_ / "file.txt"
    fi2.write_text("Sample content")    

    do1 = out / "folder"
    do1.mkdir()
    do1_1 = do1 / "subfolder1"
    do1_1.mkdir()
    doe = out / "extrafolder"
    doe.mkdir()

    fo1 = do1_1 / "subfile.txt"
    fo1.write_text("Different content")
    foe = out / "extrafile.txt"
    foe.write_text("Extra file content")

    synchronize(in_, out)

    do1_2 = out / "folder" / "subfolder2"
    fo2 = out / "file.txt"
    assert do1_2.exists() and do1_2.is_dir()
    assert not doe.exists()
    assert not foe.exists()
    assert fo2.exists()
    assert compare_files(fi1, fo1)
    assert compare_files(fi2, fo2)
    assert compare_structure(in_, out)
