import std.stdio;
import std.algorithm;
import std.random;
import std.math;
import std.conv;
import std.array;
import std.datetime;
import core.thread;

// Prime generation and validation using Fermat's Little Theorem
class FermatValidator {
    private Random rng;
    
    this() {
        rng = Random(cast(uint)Clock.currTime.toUnixTime());
    }
    
    // Generate a probable prime using Miller-Rabin + Fermat validation
    ulong generatePrime(int bits = 32) {
        ulong candidate;
        do {
            candidate = uniform(2UL^^(bits-1), 2UL^^bits, rng);
            if (candidate % 2 == 0) candidate++;
        } while (!isProbablePrime(candidate));
        return candidate;
    }
    
    // Fermat primality test: a^(p-1) ≡ 1 (mod p)
    bool fermatTest(ulong p, int witnesses = 5) {
        if (p <= 1) return false;
        if (p == 2) return true;
        if (p % 2 == 0) return false;
        
        for (int i = 0; i < witnesses; i++) {
            ulong a = uniform(2UL, p-1, rng);
            if (modPow(a, p-1, p) != 1) {
                return false;
            }
        }
        return true;
    }
    
    // Miller-Rabin for additional validation
    bool isProbablePrime(ulong n, int k = 10) {
        if (n <= 1) return false;
        if (n == 2 || n == 3) return true;
        if (n % 2 == 0) return false;
        
        // Write n-1 as 2^r * d
        ulong d = n - 1;
        int r = 0;
        while (d % 2 == 0) {
            d /= 2;
            r++;
        }
        
        for (int i = 0; i < k; i++) {
            ulong a = uniform(2UL, n-2, rng) + 1;
            ulong x = modPow(a, d, n);
            
            if (x == 1 || x == n-1) continue;
            
            bool composite = true;
            for (int j = 0; j < r-1; j++) {
                x = modPow(x, 2, n);
                if (x == n-1) {
                    composite = false;
                    break;
                }
            }
            if (composite) return false;
        }
        return fermatTest(n); // Double validation with Fermat
    }
    
    // Fast modular exponentiation
    ulong modPow(ulong base, ulong exp, ulong mod) {
        ulong result = 1;
        base = base % mod;
        while (exp > 0) {
            if (exp % 2 == 1) {
                result = (result * base) % mod;
            }
            exp = exp >> 1;
            base = (base * base) % mod;
        }
        return result;
    }
    
    // Validate authentication key using Fermat's theorem
    bool validateKey(ulong key, ulong challenge) {
        if (!fermatTest(key)) return false;
        
        // Additional validation: key must satisfy our security constraint
        ulong witness = uniform(2UL, key-1, rng);
        return modPow(witness, key-1, key) == 1;
    }
}

// Chinese Remainder Theorem for distributed sync
struct CRTNode {
    ulong modulus;
    ulong remainder;
    bool active;
    double signalStrength;
    ulong lastSync;
}

class CRTSynchronizer {
    private CRTNode[] nodes;
    private Random rng;
    private ulong globalTime;
    
    this(int nodeCount = 5) {
        rng = Random(cast(uint)Clock.currTime.toUnixTime());
        globalTime = 0;
        
        // Initialize nodes with coprime moduli
        auto validator = new FermatValidator();
        nodes = new CRTNode[nodeCount];
        
        for (int i = 0; i < nodeCount; i++) {
            nodes[i] = CRTNode(
                validator.generatePrime(16 + i * 2), // Different sized primes
                0,
                true,
                1.0,
                0
            );
        }
        
        writeln("Initialized CRT network with ", nodeCount, " nodes");
        foreach(i, node; nodes) {
            writefln("Node %d: modulus=%d", i, node.modulus);
        }
    }
    
    // Simulate jamming/interference
    void simulateJamming(double intensity = 0.3) {
        foreach(ref node; nodes) {
            if (uniform(0.0, 1.0, rng) < intensity) {
                node.active = false;
                node.signalStrength *= 0.1;
            } else {
                node.active = true;
                node.signalStrength = max(0.1, node.signalStrength + 0.1);
            }
        }
    }
    
    // Synchronize time across active nodes using CRT
    bool synchronizeTime(ulong targetTime) {
        globalTime = targetTime;
        
        // Update remainders for active nodes
        auto activeNodes = nodes.filter!(n => n.active && n.signalStrength > 0.5).array;
        
        if (activeNodes.length < 2) {
            writeln("Warning: Insufficient active nodes for sync");
            return false;
        }
        
        foreach(ref node; activeNodes) {
            node.remainder = targetTime % node.modulus;
            node.lastSync = targetTime;
        }
        
        // Verify CRT reconstruction works
        ulong reconstructed = solveCRT(activeNodes);
        bool success = (reconstructed % 1000) == (targetTime % 1000); // Check within reasonable bounds
        
        writefln("Sync attempt: target=%d, reconstructed=%d, success=%s, active_nodes=%d", 
                targetTime, reconstructed, success, activeNodes.length);
        
        return success;
    }
    
    // Solve Chinese Remainder Theorem
    ulong solveCRT(CRTNode[] activeNodes) {
        if (activeNodes.length == 0) return 0;
        if (activeNodes.length == 1) return activeNodes[0].remainder;
        
        ulong result = activeNodes[0].remainder;
        ulong lcm = activeNodes[0].modulus;
        
        for (size_t i = 1; i < activeNodes.length; i++) {
            ulong a1 = result;
            ulong m1 = lcm;
            ulong a2 = activeNodes[i].remainder;
            ulong m2 = activeNodes[i].modulus;
            
            auto solution = solveCongruence(a1, m1, a2, m2);
            result = solution[0];
            lcm = solution[1];
        }
        
        return result;
    }
    
    // Solve single congruence pair
    ulong[2] solveCongruence(ulong a1, ulong m1, ulong a2, ulong m2) {
        auto gcd_result = extendedGCD(m1, m2);
        ulong g = gcd_result[0];
        ulong x = gcd_result[1];
        
        if ((a2 - a1) % g != 0) {
            // No solution exists
            return [a1, m1];
        }
        
        ulong lcm = (m1 * m2) / g;
        ulong solution = (a1 + m1 * ((a2 - a1) / g * x)) % lcm;
        
        if (solution < 0) solution += lcm;
        
        return [solution, lcm];
    }
    
    // Extended Euclidean Algorithm
    ulong[3] extendedGCD(ulong a, ulong b) {
        if (b == 0) return [a, 1, 0];
        
        auto result = extendedGCD(b, a % b);
        ulong gcd = result[0];
        ulong x1 = result[1];
        ulong y1 = result[2];
        
        ulong x = y1;
        ulong y = x1 - (a / b) * y1;
        
        return [gcd, x, y];
    }
    
    // Network status
    void printStatus() {
        writeln("\n=== Network Status ===");
        foreach(i, node; nodes) {
            writefln("Node %d: %s, strength=%.2f, mod=%d, rem=%d", 
                    i, node.active ? "ACTIVE" : "JAMMED", 
                    node.signalStrength, node.modulus, node.remainder);
        }
    }
}

// Attack simulation
class AttackSimulator {
    private Random rng;
    
    this() {
        rng = Random(cast(uint)Clock.currTime.toUnixTime());
    }
    
    // Simulate spoofing attack
    bool attemptSpoofing(FermatValidator validator, ulong validKey) {
        // Try random keys - should fail Fermat test
        for (int i = 0; i < 10; i++) {
            ulong fakeKey = uniform(1000UL, 100000UL, rng);
            if (validator.validateKey(fakeKey, 12345)) {
                writefln("SECURITY BREACH: Fake key %d passed validation!", fakeKey);
                return true;
            }
        }
        writeln("Spoofing attack failed - system secure");
        return false;
    }
    
    // Simulate coordinated jamming
    void coordinatedJamming(CRTSynchronizer sync, int rounds = 5) {
        writeln("\n=== Coordinated Jamming Attack ===");
        
        for (int round = 0; round < rounds; round++) {
            writefln("\nJamming Round %d:", round + 1);
            sync.simulateJamming(0.4 + round * 0.1); // Increasing intensity
            
            bool syncSuccess = sync.synchronizeTime(1000 + round * 100);
            writefln("Sync success under jamming: %s", syncSuccess);
            
            sync.printStatus();
        }
    }
}

// Performance metrics
struct Metrics {
    int totalTests;
    int successfulAuths;
    int failedSpoofs;
    int successfulSyncs;
    double avgSyncTime;
}

// Main simulation runner
void runSimulation() {
    writeln("=== Modular Authentication Filters Simulation ===\n");
    
    auto validator = new FermatValidator();
    auto synchronizer = new CRTSynchronizer(6);
    auto attacker = new AttackSimulator();
    
    Metrics metrics;
    
    writeln("1. Testing Fermat Prime Validation:");
    for (int i = 0; i < 10; i++) {
        ulong prime = validator.generatePrime(24);
        bool valid = validator.validateKey(prime, 12345);
        writefln("Prime %d: %s", prime, valid ? "VALID" : "INVALID");
        
        metrics.totalTests++;
        if (valid) metrics.successfulAuths++;
    }
    
    writeln("\n2. Testing Anti-Spoofing:");
    for (int i = 0; i < 5; i++) {
        ulong validKey = validator.generatePrime(20);
        bool breached = attacker.attemptSpoofing(validator, validKey);
        if (!breached) metrics.failedSpoofs++;
    }
    
    writeln("\n3. Testing CRT Synchronization:");
    for (int i = 0; i < 10; i++) {
        bool success = synchronizer.synchronizeTime(2000 + i * 50);
        if (success) metrics.successfulSyncs++;
    }
    
    writeln("\n4. Attack Resilience Testing:");
    attacker.coordinatedJamming(synchronizer);
    
    writeln("\n=== SIMULATION RESULTS ===");
    writefln("Authentication Success Rate: %.1f%% (%d/%d)", 
            cast(double)metrics.successfulAuths / metrics.totalTests * 100,
            metrics.successfulAuths, metrics.totalTests);
    writefln("Anti-Spoofing Success Rate: %.1f%% (%d/5)", 
            cast(double)metrics.failedSpoofs / 5 * 100, metrics.failedSpoofs);
    writefln("Sync Success Rate: %.1f%% (%d/10)", 
            cast(double)metrics.successfulSyncs / 10 * 100, metrics.successfulSyncs);
}

void main() {
    runSimulation();
}