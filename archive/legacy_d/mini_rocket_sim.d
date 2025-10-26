import std.stdio;
import std.math;
import std.file;
import std.string;
import std.random;

/// Simple 3-node thermal + entropy-kernel simulation for a MEMS/FEEP "mini-rocket" head.
/// Nodes: 0=reservoir, 1=slit/emitter, 2=mount/radiator interface.

struct Plant {
    // Thermal capacities [J/K]
    double C0 = 6.0, C1 = 4.0, C2 = 10.0;
    // Conductances between nodes [W/K]
    double G01 = 0.8, G12 = 0.6;
    // Conductance from node2 to ambient (strap etc.) [W/K]
    double G2amb = 0.5;

    // Radiator properties (linearized + exact)
    double eps = 0.85;           // emissivity
    double A   = 0.01;           // m^2 radiator area (small patch)
    double Tamb = 300.0;         // K ambient/sink
    enum double sigmaSB = 5.670374419e-8; // W/m^2/K^4

    // Geometry fudge for gradient proxy (area/length weighting)
    double phiGain = 0.02; // scales ((ΔT)^2 / T^2) into W/K-ish units

    // State
    double T0 = 310.0, T1 = 307.0, T2 = 304.0; // initial temps [K]

    // Radiative heat from node2 to space/ambient (positive = leaving item)
    double QradOut(double T2_) const {
        // Exact Stefan–Boltzmann exchange to sink at Tamb
        return eps * A * (pow(T2_, 4) - pow(Tamb, 4)) * sigmaSB;
    }

    // Advance one explicit Euler step (dt small vs. time constants)
    void step(double dt, double heaterW, out double QoutBoundary) {
        // Heat flows along links (positive in the direction of first term)
        double Q01 = G01 * (T0 - T1);
        double Q12 = G12 * (T1 - T2);

        // Boundary outflows from node2 (to ambient)
        double Qcond_out = G2amb * (T2 - Tamb);      // >0 if T2 > Tamb
        double Qrad_out  = QradOut(T2);              // can be <0 if T2 < Tamb

        // Node power balances (positive raises node temp)
        double P0 = heaterW - Q01;
        double P1 = +Q01 - Q12;
        double P2 = +Q12 - Qcond_out - Qrad_out;

        // Integrate temperatures
        T0 += (P0 / C0) * dt;
        T1 += (P1 / C1) * dt;
        T2 += (P2 / C2) * dt;

        // Return total boundary heat leaving the item
        QoutBoundary = Qcond_out + Qrad_out; // W
    }

    // CIT-inspired internal generation proxy from temperature gradients
    double phiGrad() const {
        // Two links; scale by phiGain to approximate k*(gradT)^2/T^2 * volume
        double Tbar01 = 0.5 * (T0 + T1);
        double Tbar12 = 0.5 * (T1 + T2);
        double term01 = (T0 - T1) * (T0 - T1) / (Tbar01 * Tbar01 + 1e-9);
        double term12 = (T1 - T2) * (T1 - T2) / (Tbar12 * Tbar12 + 1e-9);
        return phiGain * (term01 + term12); // ~W/K
    }
}

struct Kernel {
    // Primal Logic entropy kernel parameters
    double lambda_; // 1/s
    double kappa;   // unit gain
    double dt;
    // State
    double dotS_hat = 0.0;

    this(double lambda_, double kappa, double dt) {
        this.lambda_ = lambda_;
        this.kappa   = kappa;
        this.dt      = dt;
    }

    double update(double Theta_k) {
        // Discrete exact-integrator form
        double beta = exp(-lambda_ * dt);
        dotS_hat = beta * dotS_hat + (1.0 - beta) * (kappa / lambda_) * Theta_k;
        return dotS_hat;
    }
}

void main() {
    // --- Simulation setup ---
    double dt = 0.01;           // 10 ms step
    int steps = 120_000;        // 20 minutes of sim
    int logEvery = 10;          // log each 100 ms to CSV

    Plant p;
    Kernel kT = Kernel(0.5, 1.0, dt);  // thermal kernel: tau ~ 2 s

    // Control targets
    double dotS_desired = -0.02; // target negative entropy rate [J/K/s]
    double Kp = 4.0, Ki = 0.8;   // PI gains on dotS_hat
    double heaterW = 0.0;        // actuator [W]
    double heaterMax = 6.0, heaterMin = 0.0;
    double integ = 0.0;

    // Heat-sink capacity (simple guard): cap the average boundary outflow
    double QsinkMax = 4.0; // W (radiator + strap capacity)
    double QoutBoundary = 0.0;

    // Optional multi-tone identification dither (VERY small)
    bool useDither = false;
    double dAmp = 0.05; // W RMS ~mK-level
    double w1 = 2 * PI * 0.1, w2 = 2 * PI * 0.03, w3 = 2 * PI * 0.7;

    // CSV log
    auto f = File("sim.csv", "w");
    f.writeln("t,T0,T1,T2,heaterW,Theta,dotS_hat,QoutBoundary");

    // Run
    for (int i = 0; i < steps; ++i) {
        double t = i * dt;

        // Plant step with current heater power
        p.step(dt, heaterW, QoutBoundary);

        // Entropy proxy Θ:
        //   sum(Q_in_boundary/T_boundary)  +  internal generation proxy
        // Here, boundary heat is LEAVING the item (positive QoutBoundary),
        // so heat INTO the item via boundary is negative of that.
        double Theta_boundary = -(QoutBoundary) / p.T2; // approximate T at boundary
        double Theta = Theta_boundary + p.phiGrad();    // [W/K] = J/(K*s)

        // Update kernel
        double dotS_hat = kT.update(Theta);

        // ---- CONTROL: PI on dotS_hat toward a negative target ----
        double err = dotS_hat - dotS_desired; // want dotS_hat < 0
        integ += err * dt;
        // Basic PI
        double uPI = heaterW - (Kp * err + Ki * integ);

        // Optional tiny dither for ID (kept out of controller path)
        double dither = useDither ? (dAmp * (sin(w1 * t) + 0.7 * sin(w2 * t + 1.1) + 0.5 * sin(w3 * t + 2.2))) : 0.0;

        // Apply sink guard: if boundary is over capacity, throttle commanded power
        double uCmd = clamp(uPI + dither, heaterMin, heaterMax);
        if (QoutBoundary > QsinkMax && uCmd > heaterW) {
            // limit upward slew when sink saturated
            uCmd = heaterW + 0.1 * (uCmd - heaterW); // soften increases
        }
        // Slew limit (protect emitters)
        double maxSlew = 20.0 * dt; // W/s -> W per step
        heaterW += clamp(uCmd - heaterW, -maxSlew, maxSlew);
        heaterW = clamp(heaterW, heaterMin, heaterMax);

        // Log
        if (i % logEvery == 0) {
            f.writeln(format("%.3f,%.6f,%.6f,%.6f,%.6f,%.9f,%.9f,%.6f",
                             t, p.T0, p.T1, p.T2, heaterW, Theta, dotS_hat, QoutBoundary));
        }
    }
    f.close();

    writeln("Done. Wrote sim.csv (time, temps, heater power, Theta, dotS_hat, QoutBoundary).");
}

/// Clamp helper
double clamp(double x, double lo, double hi) { return x < lo ? lo : (x > hi ? hi : x); }
	 