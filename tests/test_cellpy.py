import logging
import os
import tempfile
import time

import pytest

import cellpy.readers.core
import cellpy.utils.helpers
from cellpy import log, prms

from . import fdv

log.setup_logging(default_level="DEBUG", testing=True)


def test_conftest(hello_world):
    assert hello_world == "hello cellpy!"


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def setup_module():
    import os

    try:
        os.mkdir(fdv.output_dir)
    except Exception:
        print("could not make directory")


def test_logger(clean_dir):
    test_logging_json = os.path.join(fdv.data_dir, "test_logging.json")
    prms.Paths.filelogdir = fdv.log_dir

    log.setup_logging(testing=True)
    tmp_logger = logging.getLogger()
    assert tmp_logger.level == logging.DEBUG

    tmp_logger.info("default: testing logger (info)")
    tmp_logger.debug("default: testing logger (debug)")
    tmp_logger.error("default: testing logger (error)")

    for handler in tmp_logger.handlers:
        if handler.name == "console":
            assert handler.level == logging.CRITICAL
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_level="DEBUG", testing=True)
    tmp_logger = logging.getLogger()
    tmp_logger.info("default: testing logger (info)")
    tmp_logger.debug("default: testing logger (debug)")
    tmp_logger.error("default: testing logger (error)")

    for handler in tmp_logger.handlers:
        if handler.name == "console":
            assert handler.level == logging.DEBUG
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(default_level="INFO", testing=True)
    for handler in logging.getLogger().handlers:
        if handler.name == "console":
            assert handler.level == logging.INFO
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG

    log.setup_logging(
        default_json_path="./a_file_that_does_not_exist.json", testing=True
    )
    assert len(logging.getLogger().handlers) == 4

    log.setup_logging(default_json_path=test_logging_json, testing=True)
    log.setup_logging(custom_log_dir=clean_dir)
    tmp_logger = logging.getLogger()
    tmp_logger.info("customdir, default: testing logger (info)")
    tmp_logger.debug("customdir, default: testing logger (debug)")
    tmp_logger.error("customdir, default: testing logger (error)")


def test_logger_advanced(clean_dir):
    log.setup_logging(reset_big_log=True, testing=True)
    tmp_logger = logging.getLogger()
    tmp_logger.info("customdir, default: testing logger (info)")
    tmp_logger.debug("customdir, default: testing logger (debug)")
    tmp_logger.error("customdir, default: testing logger (error)")
    for handler in logging.getLogger().handlers:
        if handler.name == "console":
            assert handler.level == logging.CRITICAL
        if handler.name == "info_file_handler":
            assert handler.level == logging.INFO
        elif handler.name == "error_file_handler":
            assert handler.level == logging.ERROR
        elif handler.name == "debug_file_handler":
            assert handler.level == logging.DEBUG


@pytest.mark.timeout(5.0)
def test_load_and_save_resfile(clean_dir):
    import os

    from cellpy import cellreader

    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = cellpy.utils.helpers.load_and_save_resfile(f_in, None, clean_dir)
    assert os.path.isfile(new_file)


@pytest.mark.benchmark(
    group="group-name",
    min_time=0.1,
    max_time=0.5,
    min_rounds=2,
    timer=time.time,
    disable_gc=True,
    warmup=False,
)
def test_load_resfile_diagnostics(clean_dir, benchmark):
    import os

    from cellpy import cellreader, prms

    prms.Reader.diagnostics = True
    f_in = os.path.join(fdv.raw_data_dir, fdv.res_file_name)
    new_file = benchmark(
        cellpy.utils.helpers.load_and_save_resfile, f_in, None, clean_dir
    )
    assert os.path.isfile(new_file)


def test_get():
    # TODO: split into units and make more
    #   different filetypes
    #   pre and post processor hooks
    #   optional kwargs

    import cellpy

    def _my_post_processor(c):
        print(c)
        return c

    cellpy.get(
        filename=fdv.pec_file_path,
        instrument="pec_csv",
        mass=50_000,
        cycle_mode="cathode",
        testing=True,
    )
    cellpy.get(filename=fdv.cellpy_file_path, testing=True)
    cellpy.get(testing=True)
    cellpy.get(
        filename=fdv.cellpy_file_path,
        post_processor_hook=_my_post_processor,
        testing=True,
    )  # should only give a warning
    cellpy.get(
        filename=fdv.res_file_path, post_processor_hook=_my_post_processor, testing=True
    )  # should print


# @pytest.mark.unimportant
def test_humanize_bytes():

    assert cellpy.readers.core.humanize_bytes(1) == "1 byte"
    assert cellpy.readers.core.humanize_bytes(1024) == "1.0 kB"
    assert cellpy.readers.core.humanize_bytes(1024 * 123) == "123.0 kB"
    assert cellpy.readers.core.humanize_bytes(1024 * 12342) == "12.0 MB"
    assert cellpy.readers.core.humanize_bytes(1024 * 12342, 2) == "12.00 MB"
    assert cellpy.readers.core.humanize_bytes(1024 * 1234, 2) == "1.00 MB"
    assert cellpy.readers.core.humanize_bytes(1024 * 1234 * 1111, 2) == "1.00 GB"
    assert cellpy.readers.core.humanize_bytes(1024 * 1234 * 1111, 1) == "1.0 GB"


def test_example_data():
    from cellpy.utils import example_data

    a = example_data.arbin_file(testing=True)
    c = example_data.cellpy_file(testing=True)

    assert a.cell.summary.size == 522
    assert c.cell.summary.size == 1044


def teardown_module():
    import shutil

    shutil.rmtree(fdv.output_dir)
