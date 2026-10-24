import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Locale;
import java.util.SplittableRandom;

/**
 * Benchmark.java
 *
 * Synthetic election generator, correctness tests and running-time
 * experiments for the divide-and-conquer majority algorithm.
 *
 * Usage:
 *   javac MajorityVote.java Benchmark.java
 *   java Benchmark verify               # correctness tests
 *   java Benchmark bench results.csv    # timing experiments
 */
public final class Benchmark {

    /** Number of candidates on the synthetic ballot. */
    static final int CANDIDATES = 5;

    /** Ballot counts used in the timing experiments. */
    static final int[] SIZES = {
        1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000,
        500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000
    };

    /** Brute force is O(n^2), so it is only run on the smaller elections. */
    static final int BRUTE_FORCE_MAX_N = 50_000;

    static final int TRIALS = 5;

    /** Repeat a measurement until at least this much time has elapsed. */
    static final long MIN_MEASURE_NANOS = 20_000_000L;  // 20 ms

    /** Kinds of synthetic elections. */
    enum Scenario {
        LANDSLIDE,   // candidate 0 receives 60% of the ballots
        NARROW,      // candidate 0 receives floor(n/2) + 1 ballots (smallest majority)
        TIE,         // candidate 0 receives exactly floor(n/2) ballots: no majority
        FRAGMENTED   // every ballot is uniform over the 5 candidates: no majority
    }

    // ------------------------------------------------------------------
    // Synthetic data
    // ------------------------------------------------------------------

    /** Generates n shuffled ballots for the given scenario. */
    static int[] generateBallots(int n, Scenario scenario, long seed) {
        SplittableRandom rng = new SplittableRandom(seed);
        int[] ballots = new int[n];
        int leaderVotes;
        switch (scenario) {
            case LANDSLIDE:  leaderVotes = (int) (0.6 * n); break;
            case NARROW:     leaderVotes = n / 2 + 1;       break;
            case TIE:        leaderVotes = n / 2;           break;
            default:         leaderVotes = -1;              break;
        }
        if (leaderVotes < 0) {
            for (int i = 0; i < n; i++) ballots[i] = rng.nextInt(CANDIDATES);
        } else {
            leaderVotes = Math.min(leaderVotes, n);
            for (int i = 0; i < leaderVotes; i++) ballots[i] = 0;
            // Remaining ballots go to the other candidates (ids 1..4).
            for (int i = leaderVotes; i < n; i++) ballots[i] = 1 + rng.nextInt(CANDIDATES - 1);
        }
        // Fisher-Yates shuffle so the leader's ballots are spread throughout.
        for (int i = n - 1; i > 0; i--) {
            int j = rng.nextInt(i + 1);
            int t = ballots[i]; ballots[i] = ballots[j]; ballots[j] = t;
        }
        return ballots;
    }

    /** Upper bound on equality tests: 2 n ceil(log2 n) + (n - 1). */
    static long comparisonBound(int n) {
        if (n <= 1) return 0;
        int ceilLog = 32 - Integer.numberOfLeadingZeros(n - 1);
        return 2L * n * ceilLog + (n - 1);
    }

    // ------------------------------------------------------------------
    // Correctness tests
    // ------------------------------------------------------------------

    static void verify() {
        MajorityVote mv = new MajorityVote();
        long tests = 0, withMajority = 0;

        // 1. Exhaustive: every ballot sequence of length 1..8 over 3 candidates.
        for (int n = 1; n <= 8; n++) {
            int total = (int) Math.pow(3, n);
            for (int code = 0; code < total; code++) {
                int[] b = new int[n];
                int c = code;
                for (int i = 0; i < n; i++) { b[i] = c % 3; c /= 3; }
                if (check(mv, b)) withMajority++;
                tests++;
            }
        }
        System.out.printf("Exhaustive tests (n <= 8, 3 candidates): %d passed%n", tests);

        // 2. Random small elections with 1..4 candidates.
        SplittableRandom rng = new SplittableRandom(2026);
        long randomTests = 200_000;
        for (long t = 0; t < randomTests; t++) {
            int n = 1 + rng.nextInt(64);
            int k = 1 + rng.nextInt(4);
            int[] b = new int[n];
            for (int i = 0; i < n; i++) b[i] = rng.nextInt(k);
            if (check(mv, b)) withMajority++;
        }
        tests += randomTests;
        System.out.printf("Random tests (n <= 64): %d passed%n", randomTests);

        // 3. Every scenario at several sizes, including odd sizes.
        int scenarioTests = 0;
        for (Scenario s : Scenario.values()) {
            for (int n : new int[] {1, 2, 3, 7, 100, 1001, 4096, 10_007}) {
                for (long seed = 0; seed < 10; seed++) {
                    int[] b = generateBallots(n, s, seed);
                    int winner = checkWinner(mv, b);
                    if (winner != MajorityVote.NO_MAJORITY) withMajority++;
                    // The generator must produce the outcome each scenario promises.
                    boolean leaderMustWin = s == Scenario.NARROW
                            || (s == Scenario.LANDSLIDE && (int) (0.6 * n) > n / 2);
                    if (leaderMustWin && winner != 0) {
                        throw new AssertionError(s + ": candidate 0 should win, n=" + n);
                    }
                    // With n even, a tie leaves n/2 ballots for everyone else,
                    // so nobody can exceed n/2.
                    if (s == Scenario.TIE && n % 2 == 0 && winner != MajorityVote.NO_MAJORITY) {
                        throw new AssertionError("TIE produced a majority, n=" + n);
                    }
                    scenarioTests++;
                }
            }
        }
        tests += scenarioTests;
        System.out.printf("Scenario tests: %d passed%n", scenarioTests);
        System.out.printf("ALL %d TESTS PASSED (%d inputs had a majority winner)%n",
                tests, withMajority);
    }

    /**
     * Checks D&C against brute force and Boyer-Moore, and checks the
     * equality-test bound. Returns true if the input has a majority.
     */
    static boolean check(MajorityVote mv, int[] b) {
        return checkWinner(mv, b) != MajorityVote.NO_MAJORITY;
    }

    /** Same checks as check(), returning the winner (or NO_MAJORITY). */
    static int checkWinner(MajorityVote mv, int[] b) {
        mv.resetComparisons();
        int dc = mv.majorityDC(b);
        long comps = mv.getComparisons();
        int bf = mv.majorityBruteForce(b);
        int bm = mv.majorityBoyerMoore(b);
        if (dc != bf || dc != bm) {
            throw new AssertionError("Mismatch on " + java.util.Arrays.toString(b)
                    + ": dc=" + dc + " brute=" + bf + " boyerMoore=" + bm);
        }
        if (comps > comparisonBound(b.length)) {
            throw new AssertionError("Comparison bound exceeded for n=" + b.length
                    + ": " + comps + " > " + comparisonBound(b.length));
        }
        return dc;
    }

    // ------------------------------------------------------------------
    // Timing experiments
    // ------------------------------------------------------------------

    interface Solver { int solve(MajorityVote mv, int[] b); }

    static volatile int sink;  // keeps the JIT from discarding results

    static void bench(String csvPath) throws IOException {
        MajorityVote mv = new MajorityVote();

        // Warm up the JIT before measuring anything.
        int[] warm = generateBallots(1_000_000, Scenario.NARROW, 99);
        for (int i = 0; i < 15; i++) {
            sink = mv.majorityDC(warm);
            sink = mv.majorityBoyerMoore(warm);
        }
        int[] warmSmall = generateBallots(5_000, Scenario.TIE, 99);
        for (int i = 0; i < 5; i++) sink = mv.majorityBruteForce(warmSmall);

        try (PrintWriter out = new PrintWriter(new FileWriter(csvPath))) {
            out.println("algorithm,scenario,n,trial,reps,time_ms,comparisons,winner");
            for (Scenario s : Scenario.values()) {
                for (int n : SIZES) {
                    for (int trial = 0; trial < TRIALS; trial++) {
                        long seed = 1_000_003L * n + 31L * trial + s.ordinal();
                        int[] b = generateBallots(n, s, seed);

                        measure(out, mv, "DivideAndConquer", s, n, trial, b,
                                (m, x) -> m.majorityDC(x));
                        measure(out, mv, "BoyerMoore", s, n, trial, b,
                                (m, x) -> m.majorityBoyerMoore(x));
                        if (n <= BRUTE_FORCE_MAX_N) {
                            measure(out, mv, "BruteForce", s, n, trial, b,
                                    (m, x) -> m.majorityBruteForce(x));
                        }
                    }
                    System.out.printf("done %-10s n=%,d%n", s, n);
                    out.flush();
                }
            }
        }
    }

    static void measure(PrintWriter out, MajorityVote mv, String name, Scenario s,
                        int n, int trial, int[] b, Solver solver) {
        // One counted run for the comparison count and the winner.
        mv.resetComparisons();
        int winner = solver.solve(mv, b);
        long comps = mv.getComparisons();

        // Timed runs: repeat until at least MIN_MEASURE_NANOS have passed.
        int reps = 0;
        long start = System.nanoTime(), elapsed;
        do {
            sink = solver.solve(mv, b);
            reps++;
            elapsed = System.nanoTime() - start;
        } while (elapsed < MIN_MEASURE_NANOS);

        double ms = elapsed / 1e6 / reps;
        out.printf(Locale.US, "%s,%s,%d,%d,%d,%.6f,%d,%d%n",
                name, s, n, trial, reps, ms, comps, winner);
    }

    public static void main(String[] args) throws IOException {
        if (args.length >= 1 && args[0].equals("verify")) {
            verify();
        } else if (args.length >= 1 && args[0].equals("bench")) {
            bench(args.length >= 2 ? args[1] : "results.csv");
        } else {
            System.out.println("Usage: java Benchmark verify | bench [results.csv]");
        }
    }
}
