import json
from tempfile import NamedTemporaryFile

from simplemseed import FDSNSourceId
from simplemseed_obspy_plugin.core import ObsPyMSEED3DataOverflowError

from obspy import read, Stream, Trace
import numpy as np
import pytest
from io import BytesIO

from pathlib import Path


@pytest.fixture(scope='module')
def datapath(request):
    """
    Path to the 'data' directory of the current 'tests' directory
    """
    module_path = Path(request.module.__file__)
    datapath = module_path.parent / 'data'
    return datapath


class TestMSEED3ReadingAndWriting:
    """
    Test everything related to the general reading and writing of mseed3
    files.
    """

    def test_ref_data(self, datapath):
        testdir = datapath / "reference-data"
        for path in testdir.glob("*.mseed3"):
            if path.name == "reference-text.mseed3":
                # 0 not decompressible, can't return empty stream so???
                continue
            jsonpath = path.parent.joinpath(path.name[:-6] + "json")
            stream = read(path, format="MSEED3")
            assert len(stream) == 1
            trace = stream[0]
            with open(jsonpath, "r") as injson:
                jsonrec = json.load(injson)[0]

            assert jsonrec["SampleRate"] == trace.stats.sampling_rate
            assert jsonrec["PublicationVersion"] == trace.stats.mseed3.pubVer
            sid = FDSNSourceId.fromNslc(
                trace.stats.network,
                trace.stats.station,
                trace.stats.location,
                trace.stats.channel,
            )
            assert jsonrec["SID"] == str(sid)
            if "ExtraHeaders" in jsonrec:
                assert "eh" in trace.stats.mseed3
                assert jsonrec["ExtraHeaders"] == trace.stats.mseed3.eh
            if jsonrec["DataLength"] > 0:
                assert jsonrec["SampleCount"] == len(trace)
                jsondata = jsonrec["Data"]
                assert len(jsondata) == len(trace)
                for i in range(len(jsondata)):
                    assert jsondata[i] == trace[i]

    def test_read_file_via_obspy(self, datapath):
        """
        Read file test via L{obspy.core.Stream}.
        """
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        assert len(stream) == 6
        assert stream[0].stats.network == "CO"
        assert stream[0].stats.station == "BIRD"
        assert stream[0].stats.location == "00"
        assert stream[0].stats.channel == "HHE"
        assert str(stream[0].data) == "[ 401  630  750 ... 1877 1019 1659]"
        # This is controlled by the stream[0].data attribute.
        assert stream[0].stats.npts == 3000
        assert stream[0].data.dtype == np.int32

    def test_write_int32(self, datapath):
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        outfile = datapath / "bird_jsc_recomp_int32.ms3"
        stream.write(outfile, format="MSEED3", encoding="INT32")
        redo = read(outfile, format="MSEED3")
        self._check_bird_jsc(stream, redo)
        assert stream[0].data.dtype == np.int32
        assert redo[0].data.dtype == np.int32

    def test_write_float32(self, datapath):
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        with NamedTemporaryFile() as tf:
            outfile = tf.name
            stream.write(outfile, format="MSEED3", encoding="FLOAT32")
            redo = read(outfile, format="MSEED3")
        self._check_bird_jsc(stream, redo)
        assert redo[0].data.dtype == np.float32

    def test_write_float64(self, datapath):
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        with NamedTemporaryFile() as tf:
            outfile = tf.name
            stream.write(outfile, format="MSEED3", encoding="FLOAT64")
            redo = read(outfile, format="MSEED3")
        self._check_bird_jsc(stream, redo)
        assert redo[0].data.dtype == np.float64

    def test_write_steim1(self, datapath):
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        with NamedTemporaryFile() as tf:
            outfile = tf.name
            stream.write(outfile, format="MSEED3", encoding="STEIM1")
            redo = read(outfile, format="MSEED3")
        self._check_bird_jsc(stream, redo)
        assert redo[0].data.dtype == np.int32

    def test_write_steim2(self, datapath):
        testfile = datapath / "bird_jsc.ms3"
        stream = read(testfile, format="MSEED3")
        with NamedTemporaryFile() as tf:
            outfile = tf.name
            stream.write(outfile, format="MSEED3", encoding="STEIM2")
            redo = read(outfile, format="MSEED3")
        self._check_bird_jsc(stream, redo)
        assert redo[0].data.dtype == np.int32

    def _check_bird_jsc(self, stream_a, stream_b):
        assert len(stream_a) == 6
        assert len(stream_b) == 6
        for st_idx in range(len(stream_b)):
            assert stream_a[st_idx].stats.network == stream_b[st_idx].stats.network
            assert stream_a[st_idx].stats.station == stream_b[st_idx].stats.station
            assert stream_a[st_idx].stats.location == stream_b[st_idx].stats.location
            assert stream_a[st_idx].stats.channel == stream_b[st_idx].stats.channel
            assert len(stream_a[st_idx].data) == len(stream_b[st_idx].data)
            for i in range(len(stream_b[st_idx].data)):
                assert stream_a[st_idx].data[i] == stream_b[st_idx].data[i]

    def test_fail_steim_for_float(self, datapath):
        data = np.array([1.1, 2, 3], dtype="float32")
        tr = Trace(data)
        stream = Stream([tr])
        with pytest.raises(Exception):
            with NamedTemporaryFile() as tf:
                stream.write(tf.name, format="MSEED3", encoding="STEIM1")
        with pytest.raises(Exception):
            with NamedTemporaryFile() as tf:
                stream.write(tf.name, format="MSEED3", encoding="STEIM2")

    def test_guess_encoding(self, datapath):
        tr = Trace(np.array([1, 2, 3, -17], dtype="int64"))
        stream = Stream([tr])
        # guess output encoding
        with BytesIO() as buf:
            stream.write(buf, format="MSEED3")
            buf.seek(0)
            in_stream = read(buf)
        assert in_stream[0].data.dtype == np.int32
        assert np.array_equal(stream[0].data, in_stream[0].data)
        tr = Trace(np.array([1.1, 2.2, 3.3, -17.1], dtype="float32"))
        stream = Stream([tr])
        # guess output encoding
        with BytesIO() as buf:
            stream.write(buf, format="MSEED3")
            buf.seek(0)
            in_stream = read(buf)
        assert in_stream[0].data.dtype == np.float32
        assert np.array_equal(stream[0].data, in_stream[0].data)
        tr = Trace(np.array([1.1, 2.2, 3.3, -17.1, 2**55], dtype="float64"))
        stream = Stream([tr])
        # guess output encoding
        with BytesIO() as buf:
            stream.write(buf, format="MSEED3")
            buf.seek(0)
            in_stream = read(buf)
        assert in_stream[0].data.dtype == np.float64
        assert np.array_equal(stream[0].data, in_stream[0].data)

    def test_fail_overflow(self, datapath):
        x = 2**55
        data = [1, 2, -3, x, -1]
        # should fail as python int list to numpy array checks values can fit
        with pytest.raises(OverflowError):
            np.array(data, dtype=np.int32)
        data_i64 = np.array(data, dtype=np.int64)

        # numpy ndarray.astype() does not check values fitting for
        # int64 -> int32 conversion
        tr = Trace(data_i64)
        stream = Stream([tr])
        with pytest.raises(ObsPyMSEED3DataOverflowError):
            with NamedTemporaryFile() as tf:
                stream.write(tf.name, format="MSEED3", encoding="INT32")
