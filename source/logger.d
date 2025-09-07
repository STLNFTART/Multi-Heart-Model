module logger;
import std.stdio;

struct Csv {
    File f;
    this(string path, string header) { f = File(path, "w"); f.writeln(header); }
    void row(T...)(T vals) {
        foreach (i, v; vals) {
            if (i) f.write(',');
            f.write(v);
        }
        f.writeln();
    }
    ~this() { try f.close(); catch(Throwable) {} }
}
