module models.poiseuille;
import common, primal, std.math;

RHS poiseuilleRHS(PLConfig plc){
    return (double t, const(double[]) x, const(double)[] th){
        // x=[Q]; th=[ΔP, μ, L, r]
        double Q=x[0];
        double dP=th[0], mu=th[1], L=th[2], r=th[3];
        double Qss = (M_PI * pow(r,4) * dP) / (8.0 * mu * L);
        double k = 5.0;
        double dQ = k*(Qss - Q);

        final switch(plc.mode){
            case PLMode.Residual: dQ += R(Q,t,plc); break;
            case PLMode.ParamMod: r *= M(Q,t,plc);
                                  Qss = (M_PI * pow(r,4) * dP) / (8.0 * mu * L);
                                  dQ = k*(Qss - Q); break;
            case PLMode.Control:  dQ += U(t,plc); break;
            case PLMode.TimeWarp: break;
        }
        return [dQ];
    };
}
