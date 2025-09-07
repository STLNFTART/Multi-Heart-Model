module app;
import std.stdio;
import std.math : fabs;
import common, primal, logger;
static import models.mm;
static import models.sir;
static import models.fhn;
static import models.nernst;
static import models.poiseuille;

struct RunCfg { PLMode mode; double alpha, lambda; }

void runMM(ref Csv log, RunCfg c){
    auto plc = PLConfig(c.mode, c.alpha, c.lambda);
    auto f = models.mm.mmRHS(plc);
    double dt=1e-3; size_t steps=10_000;
    double[] x0=[1.0,0.0]; double[] th=[1.0,0.5];
    auto xT = (plc.mode==PLMode.TimeWarp) ? rk4Warp(f,0.0,x0,dt,steps,th,plc)
                                          : rk4    (f,0.0,x0,dt,steps,th);
    log.row("MM", plc.mode, plc.alpha, plc.lambda, xT[0], xT[1]);
}

void runSIR(ref Csv log, RunCfg c){
    auto plc = PLConfig(c.mode, c.alpha, c.lambda);
    auto f = models.sir.sirRHS(plc);
    double dt=1e-2; size_t steps=10_000;
    double N=1000, S0=N-1, I0=1, R0=0;
    double[] x0=[S0,I0,R0]; double[] th=[0.3,0.1,N];
    auto xT = (plc.mode==PLMode.TimeWarp) ? rk4Warp(f,0.0,x0,dt,steps,th,plc)
                                          : rk4    (f,0.0,x0,dt,steps,th);
    log.row("SIR", plc.mode, plc.alpha, plc.lambda, xT[0], xT[1], xT[2]);
    double err = fabs((xT[0]+xT[1]+xT[2]) - N);
    log.row("SIR_mass_err", plc.mode, plc.alpha, plc.lambda, err);
}

void runFHN(ref Csv log, RunCfg c){
    auto plc = PLConfig(c.mode, c.alpha, c.lambda);
    auto f = models.fhn.fhnRHS(plc);
    double dt=1e-3; size_t steps=50_000;
    double[] x0=[-1.0, 1.0]; double[] th=[0.7, 0.8, 12.5];
    auto xT = (plc.mode==PLMode.TimeWarp) ? rk4Warp(f,0.0,x0,dt,steps,th,plc)
                                          : rk4    (f,0.0,x0,dt,steps,th);
    log.row("FHN", plc.mode, plc.alpha, plc.lambda, xT[0], xT[1]);
}

void main(){
    Csv log = Csv("results.csv","model,mode,alpha,lambda,val1,val2,val3");
    auto modes   = [PLMode.Residual, PLMode.ParamMod, PLMode.Control, PLMode.TimeWarp];
    auto alphas  = [-0.1, 0.0, 0.1];
    auto lambdas = [0.5, 1.0, 1.5, 2.0];
    foreach (m; modes) foreach (a; alphas) foreach (l; lambdas) {
        auto c = RunCfg(m,a,l);
        runMM(log, c);
        runSIR(log, c);
        runFHN(log, c);
        runNernst(log, c);
        runPoiseuille(log, c);
    }
    writeln("wrote results.csv");
}

void runNernst(ref Csv log, RunCfg c){
    auto plc=PLConfig(c.mode,c.alpha,c.lambda);
    auto f=models.nernst.nernstRHS(plc);
    double dt=1e-2; size_t steps=20_000;
    double[] x0=[-0.07];                 // initial E (V)
    double[] th=[310.0,1.0,145.0,15.0];  // T[K], z, Co, Ci
    auto xT=(plc.mode==PLMode.TimeWarp)? rk4Warp(f,0.0,x0,dt,steps,th,plc)
                                       : rk4    (f,0.0,x0,dt,steps,th);
    log.row("NERNST", plc.mode, plc.alpha, plc.lambda, xT[0]);
}

void runPoiseuille(ref Csv log, RunCfg c){
    auto plc=PLConfig(c.mode,c.alpha,c.lambda);
    auto f=models.poiseuille.poiseuilleRHS(plc);
    double dt=1e-2; size_t steps=20_000;
    double[] x0=[0.0];
    // th=[ΔP, μ, L, r]  units arbitrary but consistent
    double[] th=[100.0, 3.5, 10.0, 0.5];
    auto xT=(plc.mode==PLMode.TimeWarp)? rk4Warp(f,0.0,x0,dt,steps,th,plc)
                                       : rk4    (f,0.0,x0,dt,steps,th);
    log.row("POISEUILLE", plc.mode, plc.alpha, plc.lambda, xT[0]);
}
