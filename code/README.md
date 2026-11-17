# Computational laboratory

From the course directory, `python code/lab.py all` runs the ten deterministic model checks. The program takes only a lab name, prints the main results, and exits on a failed assertion. Its circuit models use invented parameters for explanatory purposes.

`ngspice -b code/rc.cir` independently simulates the RC transient from Chapter 2. The capacitor starts at 0.8 V. The measurements check the 0.4 V crossing and the time between 0.72 V and 0.08 V. Compare the measured values with 27.73 ps and 87.89 ps. The deck is a linear circuit, so it excludes MOS slew dependence and device parasitics.

For the synthesis and equivalence exercises, run `yosys -s code/synthesis.ys` with Yosys on the path and a `work/` folder in the course directory. The same script runs with `yowasp-yosys` when using the WebAssembly build. It checks the elaborated design, maps to Yosys generic gates, and writes `work/execution_slice_mapped.v`. It then checks the eight matched output bits by induction and verifies the starting post-reset steps with a sequential miter. Finally it proves the selector relocation combinationally and obtains a 13-versus-16 counterexample for the reversed selector. The state contract and reset argument appear in Chapter 11. This generic-gate exercise supplies no characterized cell delays or physical parasitics.

[Yosys synthesis](https://github.com/YosysHQ/yosys/blob/main/docs/source/using_yosys/synthesis/synth.rst) · [Yosys model checking](https://github.com/YosysHQ/yosys/blob/main/docs/source/using_yosys/more_scripting/model_checking.rst) · [ngspice project](https://ngspice.sourceforge.io/)
