module models.nernst;
import common, primal, std.math;

RHS nernstRHS(PLConfig plc){
    return (double t, const(double[]) x, const(double)[] th){
        // x=[E]; th=[T,z,Co,Ci]
        double E=x[0];
        double T=th[0], z=th[1], Co=th[2], Ci=th[3];
        enum Rgas = 8.314462618;
        enum F    = 96485.33212;

        double EN = (Rgas*T/(z*F)) * log(Co/Ci);
        double k = 10.0;
        double dE = k*(EN - E);

        final switch(plc.mode){
            case PLMode.Residual: dE += R(E,t,plc); break;
            case PLMode.ParamMod:
                T *= M(E,t,plc);
                EN = (Rgas*T/(z*F)) * log(Co/Ci);
                dE = k*(EN - E); break;
            case PLMode.Control:  dE += U(t,plc); break;
            case PLMode.TimeWarp: break;
        }
        return [dE];
    };
}
