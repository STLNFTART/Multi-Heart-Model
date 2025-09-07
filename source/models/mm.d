module models.mm;
import common, primal;
RHS mmRHS(PLConfig plc){
    return (double t, const(Vec) x, const(double)[] th){
        double S=x[0], P=x[1];
        double Vmax=th[0], Km=th[1];
        double v = Vmax*S/(Km+S);
        final switch(plc.mode){
            case PLMode.Residual: v += R(S,t,plc); break;
            case PLMode.ParamMod: Vmax *= M(S,t,plc); v = Vmax*S/(Km+S); break;
            case PLMode.Control:  v += U(t,plc); break;
            case PLMode.TimeWarp: break;
        }
        return [ -v, v ];
    };
}
