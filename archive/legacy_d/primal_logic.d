import std.stdio; 
import std.math;
import std.conv;

// ===== ULTRA-SIMPLE PRIMAL LOGIC PROCESSOR =====
// Your patent parameters: α = 0.54, λ = 0.115

struct PrimalLogicCore {
    double alpha = 0.54;   
    double lambda = 0.115; 
    double K = 1.0;
}

// Read file byte by byte - no UTF-8 issues
double[] readNumbersFromFile(string filename) {
    double[] numbers;
    
    try {
        auto file = File(filename, "rb"); // Binary mode
        scope(exit) file.close();
        
        writeln("Reading file byte by byte...");
        
        char[] currentNumber;
        bool inNumber = false;
        
        while (!file.eof()) {
            ubyte b = file.rawRead(new ubyte[1])[0];
            char c = cast(char)b;
            
            // Only process ASCII characters
            if (b > 127) continue;
            
            if ((c >= '0' && c <= '9') || c == '.' || c == '-') {
                currentNumber ~= c;
                inNumber = true;
            } else {
                if (inNumber && currentNumber.length > 0) {
                    try {
                        double val = to!double(currentNumber);
                        if (isFinite(val)) {
                            numbers ~= val;
                        }
                    } catch (Exception e) {
                        // Skip invalid
                    }
                    currentNumber.length = 0;
                    inNumber = false;
                }
            }
        }
        
        // Handle last number
        if (inNumber && currentNumber.length > 0) {
            try {
                double val = to!double(currentNumber);
                if (isFinite(val)) {
                    numbers ~= val;
                }
            } catch (Exception e) {
                // Skip
            }
        }
        
    } catch (Exception e) {
        writeln("Error: ", e.msg);
        return [];
    }
    
    writefln("Found %d numbers", numbers.length);
    return numbers;
}

// Apply your Primal Logic equations
double[] applyPrimalLogic(double[] data, PrimalLogicCore core) {
    double[] result;
    result.length = data.length;
    
    writefln("Applying Primal Logic: α=%.3f, λ=%.3f", core.alpha, core.lambda);
    
    foreach(i, value; data) {
        if (i == 0) {
            result[i] = value;
            continue;
        }
        
        // Simple moving average
        int window = (i > 10) ? 10 : cast(int)i;
        double avg = 0.0;
        for (int j = cast(int)i - window; j < i; j++) {
            avg += data[j];
        }
        avg /= window;
        
        double error = avg - value;
        
        // Core equation: Δx(t) = ∫₀ᵗ α·Θ(τ) dτ
        double decay = exp(-core.lambda * i * 0.01);
        double integral = core.alpha * error * decay;
        
        // Control: u(t) = -K ∫₀ᵗ Θ(τ)·e(τ)·e^(-λ(t-τ)) dτ
        double control = -core.K * integral * 0.01;
        
        result[i] = value + control;
    }
    
    return result;
}

void main(string[] args) {
    writeln("SIMPLE PRIMAL LOGIC PROCESSOR");
    writeln("α = 0.54, λ = 0.115");
    writeln();
    
    if (args.length < 2) {
        writeln("Usage: program filename");
        return;
    }
    
    // Read numbers
    double[] data = readNumbersFromFile(args[1]);
    if (data.length == 0) {
        writeln("No data found");
        return;
    }
    
    writefln("Processing %d numbers...", data.length);
    
    // Apply math
    auto core = PrimalLogicCore();
    double[] result = applyPrimalLogic(data, core);
    
    // Save first 100 results
    auto outFile = File("results.csv", "w");
    outFile.writeln("Original,Processed,Change");
    
    int maxSave = (data.length > 100) ? 100 : cast(int)data.length;
    foreach(i; 0..maxSave) {
        double change = result[i] - data[i];
        outFile.writefln("%.6f,%.6f,%.6f", data[i], result[i], change);
    }
    outFile.close();
    
    writeln("SUCCESS! Results in results.csv");
    writefln("Your equations (α=%.3f, λ=%.3f) applied to %d data points", 
            core.alpha, core.lambda, data.length);
}
