# simplemseed_obspy_plugin
Obspy plugin for reading miniseed3 files.

See https://pypi.org/project/simplemseed/ for details.


## Installation

Install ObsPy, then

```bash
pip install simplemseed_obspy_plugin
```


## Usage

It will hook into ObsPy's normal I/O handling and you just use it as you would
use any format:

```
>>> import obspy
>>> st = obspy.read("src/simplemseed_obspy_plugin/tests/data/bird_jsc.ms3")
>>> for t in st:
...   print(t)
...
CO.BIRD.00.HHE | 2024-02-06T11:30:00.009998Z - 2024-02-06T11:30:29.999998Z | 100.0 Hz, 3000 samples
CO.BIRD.00.HHN | 2024-02-06T11:30:00.009998Z - 2024-02-06T11:30:29.999998Z | 100.0 Hz, 3000 samples
CO.BIRD.00.HHZ | 2024-02-06T11:30:00.009998Z - 2024-02-06T11:30:29.999998Z | 100.0 Hz, 3000 samples
CO.JSC.00.HHE | 2024-02-06T11:30:00.008392Z - 2024-02-06T11:30:29.998392Z | 100.0 Hz, 3000 samples
CO.JSC.00.HHN | 2024-02-06T11:30:00.008392Z - 2024-02-06T11:30:29.998392Z | 100.0 Hz, 3000 samples
CO.JSC.00.HHZ | 2024-02-06T11:30:00.008392Z - 2024-02-06T11:30:29.998392Z | 100.0 Hz, 3000 samples
>>> st.write("out.ms3", format="mseed3")
```
