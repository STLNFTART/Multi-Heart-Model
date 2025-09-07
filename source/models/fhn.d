module models.fhn;
import common, primal;

RHS fhnRHS(PLConfig plc){
    return (double t, const(double[]) x, const(double)[] th){
        // x=[v,w], th=[a,b,c]
        double v=x[0], w=x[1], a=th[0], b=th[1], c=th[2];
        double dv = v - v*v*v/3.0 - w;
        double dw = (v + a - b*w) / c;

        final switch(plc.mode){
            case PLMode.Residual:
                dv += R(v,t,plc); dw += R(w,t,plc); break;
            case PLMode.ParamMod:
                a *= M(v,t,plc); b *= M(w,t,plc);
                dv = v - v*v*v/3.0 - w;
                dw = (v + a - b*w) / c; break;
            case PLMode.Control:
                dv += U(t,plc); break;
            case PLMode.TimeWarp:
                break;
        }
        return [dv, dw];
    };
}
