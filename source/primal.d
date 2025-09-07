module primal;
import std.math;
enum PLMode { Residual, ParamMod, Control, TimeWarp }
struct PLConfig { PLMode mode; double alpha, lambda; }
double R(double x, double t, PLConfig c){ return c.alpha*sin(c.lambda*t)*x; }
double M(double x, double t, PLConfig c){ return 1.0 + c.alpha*tanh(c.lambda*x); }
double U(double t, PLConfig c){ return c.alpha*cos(c.lambda*t); }
double G(double t, PLConfig c){ return fmax(1e-6, 1.0 + c.alpha*sin(c.lambda*t)); }
