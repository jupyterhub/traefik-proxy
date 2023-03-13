# Performance benchmarks

This folder contains tools for measuring performance of jupyterhub-traefik-proxy.
We have a few measurements of the performance of the JupyterHub Proxy API (measuring our code),
and some measurements of the throughput handling (measuring traefik itself).

To collect a single measurement, run `python3 check_perf.py` (see `python3 check_perf.py --help` for options).
Or to collect all measurements for several implementations and store the results in `results/*.CSV`, run `bash run_benchmarks.sh`.

`bootstrap-vm.sh` contains some installation steps to get a cloud VM set up to run the benchmarks.

Results are stored as CSV in `results/`, and can be explored and explained in [ProxyPerformance.ipynb](ProxyPerformance.ipynb).
