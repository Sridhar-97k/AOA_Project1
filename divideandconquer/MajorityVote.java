/**
 * MajorityVote.java
 *
 * Divide-and-conquer verification of an election majority.
 *
 * Model: ballots can only be tested for equality ("are these two ballots
 * for the same candidate?"). No sorting and no tally table are used.
 * Each ballot is stored as a candidate id (int >= 0), but the algorithms
 * below only ever look at two ballots through same(), which counts every
 * equality test so the experiments can report it.
 *
 * A candidate x is the majority winner of n ballots if it appears on
 * more than n/2 of them. Methods return NO_MAJORITY (-1) when no such
 * candidate exists.
 */
public final class MajorityVote {

    /** Returned when no candidate holds more than half the ballots. */
    public static final int NO_MAJORITY = -1;

    /** Number of equality tests performed since the last reset. */
    private long comparisons = 0;

    public long getComparisons() { return comparisons; }
    public void resetComparisons() { comparisons = 0; }

    /** The only way the algorithms inspect ballots: one equality test. */
    private boolean same(int a, int b) {
        comparisons++;
        return a == b;
    }

    // ------------------------------------------------------------------
    // Divide-and-conquer algorithm
    // ------------------------------------------------------------------

    /** Majority winner of all ballots, or NO_MAJORITY. */
    public int majorityDC(int[] ballots) {
        if (ballots.length == 0) return NO_MAJORITY;
        return majorityDC(ballots, 0, ballots.length);
    }

    /**
     * Majority winner of ballots[lo..hi) (hi exclusive), or NO_MAJORITY.
     * Requires hi - lo >= 1.
     */
    private int majorityDC(int[] ballots, int lo, int hi) {
        // Base case: a single ballot is its own majority.
        if (hi - lo == 1) return ballots[lo];

        // Divide: split the ballots into two halves.
        int mid = (lo + hi) >>> 1;

        // Conquer: each half reports its own majority winner (or none).
        int left = majorityDC(ballots, lo, mid);
        int right = majorityDC(ballots, mid, hi);

        // Combine.
        // Neither half has a winner, so the whole cannot have one (Lemma 1).
        if (left == NO_MAJORITY && right == NO_MAJORITY) return NO_MAJORITY;

        // Both halves agree: that candidate holds more than half of each
        // half, hence more than half of the whole.
        if (left != NO_MAJORITY && right != NO_MAJORITY && same(left, right)) {
            return left;
        }

        // Otherwise recount the (at most two) finalists over the whole range.
        int half = (hi - lo) / 2;  // count > n/2  <=>  count > floor(n/2)
        if (left != NO_MAJORITY && count(ballots, lo, hi, left) > half) return left;
        if (right != NO_MAJORITY && count(ballots, lo, hi, right) > half) return right;
        return NO_MAJORITY;
    }

    /** Number of ballots in ballots[lo..hi) cast for candidate x. */
    private int count(int[] ballots, int lo, int hi, int x) {
        int c = 0;
        for (int i = lo; i < hi; i++) {
            if (same(ballots[i], x)) c++;
        }
        return c;
    }

    // ------------------------------------------------------------------
    // Baselines (used for verification and comparison only)
    // ------------------------------------------------------------------

    /** Brute force, O(n^2): recount every ballot's candidate. */
    public int majorityBruteForce(int[] ballots) {
        int n = ballots.length;
        for (int i = 0; i < n; i++) {
            if (count(ballots, 0, n, ballots[i]) > n / 2) return ballots[i];
        }
        return NO_MAJORITY;
    }

    /** Boyer-Moore voting algorithm, O(n): one pairing pass + one recount. */
    public int majorityBoyerMoore(int[] ballots) {
        int n = ballots.length;
        if (n == 0) return NO_MAJORITY;
        int candidate = ballots[0];
        int lead = 0;
        for (int i = 0; i < n; i++) {
            if (lead == 0) {
                candidate = ballots[i];
                lead = 1;
            } else if (same(ballots[i], candidate)) {
                lead++;
            } else {
                lead--;
            }
        }
        return count(ballots, 0, n, candidate) > n / 2 ? candidate : NO_MAJORITY;
    }
}
