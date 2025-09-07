module common;

alias Vec = double[];
alias RHS = Vec delegate(double t, const(Vec) x, const(double)[] theta);

private Vec addScaled(const(Vec) a, const(Vec) b, double s) {
    auto c = a.dup; foreach (i; 0 .. c.length) c[i] += s*b[i]; return c;
}

Vec rk4(RHS f, double t0, Vec x0, double dt, size_t steps, const(double)[] th) {
    auto x = x0.dup; double t=t0;
    foreach (_; 0 .. steps) {
        auto k1 = f(t,          x,                      th);
        auto k2 = f(t+0.5*dt,   addScaled(x,k1,0.5*dt), th);
        auto k3 = f(t+0.5*dt,   addScaled(x,k2,0.5*dt), th);
        auto k4 = f(t+dt,       addScaled(x,k3,dt),     th);
        foreach (i; 0 .. x.length)
            x[i] += dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6.0;
        t += dt;
    }
    return x;
}

import primal; // for G, PLConfig

Vec rk4Warp(RHS f, double t0, Vec x0, double dt, size_t steps,
            const(double)[] th, PLConfig plc) {
    auto x = x0.dup; double t=t0;
    foreach (_; 0 .. steps) {
        auto dti = dt * G(t, plc);           // per-step warp
        auto k1 = f(t,           x,                       th);
        auto k2 = f(t+0.5*dti,   addScaled(x,k1,0.5*dti), th);
        auto k3 = f(t+0.5*dti,   addScaled(x,k2,0.5*dti), th);
        auto k4 = f(t+dti,       addScaled(x,k3,dti),     th);
        foreach (i; 0 .. x.length)
            x[i] += dti*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6.0;
        t += dti;
    }
    return x;
}
