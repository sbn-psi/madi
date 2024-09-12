import os


def rebase_filenames(basepath, filenames):
    return [os.path.join(basepath, filename) for filename in filenames]
