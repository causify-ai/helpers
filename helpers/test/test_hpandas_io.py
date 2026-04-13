import logging
import os

import pytest

import helpers.hpandas as hpandas
import helpers.hs3 as hs3
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# TestReadDataFromS3
# #############################################################################


class TestReadDataFromS3(hunitest.TestCase):
    def test_read_csv1(self) -> None:
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_name = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            # TODO(sonaal): Reorganize all s3 input data, CmampTask5650.
            "alphamatic-data",
            "data/kibot/all_stocks_1min/RIMG.csv.gz",
        )
        hs3.dassert_path_exists(file_name, s3fs)
        stream, kwargs = hs3.get_local_or_s3_stream(file_name, s3fs=s3fs)
        hpandas.read_csv_to_df(stream, **kwargs)

    @pytest.mark.slow("~15 sec.")
    def test_read_parquet1(self) -> None:
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_name = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "data/kibot/pq/sp_500_1min/AAPL.pq",
        )
        hs3.dassert_path_exists(file_name, s3fs)
        stream, kwargs = hs3.get_local_or_s3_stream(file_name, s3fs=s3fs)
        hpandas.read_parquet_to_df(stream, **kwargs)
