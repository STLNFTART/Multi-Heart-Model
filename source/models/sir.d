module models.sir;
import common, primal;

RHS sirRHS(PLConfig plc){
    return (double t, const(Vec) x, const(double)[] th){
        // x=[S,I,Rc], th=[beta,gamma,N]
        double S=x[0], I=x[1], Rc=x[2];
        double beta=th[0], gamma=th[1], N=th[2];

        double inf = beta*S*I/N;
        double rec = gamma*I;
        double dS=-inf, dI=inf-rec, dRc=rec;

        final switch(plc.mode){
            case PLMode.Residual:
                dS  += R(S,t,plc);
                dI  += R(I,t,plc);
                dRc += R(Rc,t,plc);
                break;
            case PLMode.ParamMod:
                beta *= M(I,t,plc);
                inf = beta*S*I/N;
                dS=-inf; dI=inf-rec; dRc=rec;
                break;
            case PLMode.Control:
                dI += U(t,plc);
                break;
            case PLMode.TimeWarp:
                break;
        }
        return [dS,dI,dRc];
    };
}
