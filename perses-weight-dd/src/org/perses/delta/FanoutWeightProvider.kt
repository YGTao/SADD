
package org.perses.delta

import org.perses.spartree.AbstractSparTreeNode
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.max

/**
 * Unified weight for WDD/HDD:
 *
 *   W = ⌊ V · ( 1 + λS · S + λSB · ( S · φ(B) ) ) ⌋ + 1
 *
 * where
 *   V        = depth × leaves            // rectangle volume (max depth × #leaves)
 *   S        = E[ H(u)/ln k(u) | k(u)≥2] // decision uniformity in [0,1]
 *   B        = E[ e^{H(u)} - 1 | k(u)≥2] // expected extra effective branches
 *   φ(B)     = B / (B + C) ∈ (0,1)       // saturation to keep scale stable
 *
 * Recommended settings for your experiments:
 *   - Version A (equal weights):        λS = 1.0, λSB = 1.0,  C = 3.0
 *   - Version B (half-half weights):    λS = 0.5, λSB = 0.5,  C = 3.0
 *
 * Notes:
 *   - S captures “how uniform” branching is (but not how many branches).
 *   - B captures “how many effective branches” (via e^{H}), i.e., expected candidates
 *     you’ll face when refining after a failed deletion; φ(B) keeps it bounded.
 *   - Multiplying by V keeps the overall unit consistent and preserves “equal-split” semantics.
 */
class FanoutWeightProvider(
    private val lambdaS: Double = 1.0,     // coefficient for S·V
    private val lambdaSB: Double = 1.0,    // coefficient for S·φ(B)·V
    private val cSaturation: Double = 16.0, // C in φ(B)=B/(B+C); 
    private val useEntropy: Boolean = true,
    private val useBranchLoad: Boolean = true
) : WeightSplitDeltaDebugger.IWeightProvider<AbstractSparTreeNode>,
    WeightedDeltaDebugger.IWeightProvider<AbstractSparTreeNode> {

    private val cache = mutableMapOf<AbstractSparTreeNode, Metrics>()

    override fun weight(element: AbstractSparTreeNode): Int {
        val m = computeMetrics(element)

        // Volume: depth × leaves (leaves == #leaf nodes == max level width)
        val V = m.depth * m.leaves

        // Decision uniformity S in [0,1]
        val S = if (useEntropy && m.sDen > 0.0) m.sNum / m.sDen else 0.0

        // Effective-branch increment B (unbounded), squashed to φ(B) ∈ [0,1)
        val B = if (useBranchLoad && m.bDen > 0.0) m.bNum / m.bDen else 0.0
        val phiB = if (useBranchLoad && B > 0.0) B / (B + cSaturation) else 0.0

        // Factor = 1 + λS·S + λSB·(S·φ(B))
        val factor = 1.0 + lambdaS * S + lambdaSB * (S * phiB)

        val raw = V.toDouble() * factor
        val w = raw.toInt() + 1 // strictly positive integer for WDD compatibility

        // println(
        //     "[DEBUG] Node=${element::class.simpleName} | depth=${m.depth} | leaves=${m.leaves} | " +
        //     "V=$V | S=%.4f | B=%.4f | phi(B)=%.4f | factor=%.4f | weight=$w"
        //         .format(S, B, phiB, factor)
        // )
        return w
    }

    fun clearCache() = cache.clear()

    // ---- single-pass DFS aggregating depth, leaves, and stats for S & B ----

    private data class Metrics(
        val depth: Int,    // max distance to a leaf (leaf depth = 0)
        val leaves: Int,   // # leaves in subtree
        val sNum: Double,  // Σ leaves(u) * [ H(u)/ln k(u) ] over decision nodes
        val sDen: Double,  // Σ leaves(u) over decision nodes
        val bNum: Double,  // Σ leaves(u) * [ e^{H(u)} - 1 ] over decision nodes
        val bDen: Double   // Σ leaves(u) over decision nodes
    )

    private fun computeMetrics(node: AbstractSparTreeNode): Metrics {
        return cache.getOrPut(node) {
            val children = node.immutableChildView
            if (children.isEmpty()) {
                // Leaf
                Metrics(depth = 0, leaves = 1, sNum = 0.0, sDen = 0.0, bNum = 0.0, bDen = 0.0)
            } else {
                var maxChildDepth = 0
                var sumLeaves = 0
                var accSNum = 0.0
                var accSDen = 0.0
                var accBNum = 0.0
                var accBDen = 0.0

                val childM = ArrayList<Metrics>(children.size)
                for (ch in children) {
                    val cm = computeMetrics(ch)
                    childM += cm
                    maxChildDepth = max(maxChildDepth, cm.depth)
                    sumLeaves += cm.leaves
                    accSNum += cm.sNum
                    accSDen += cm.sDen
                    accBNum += cm.bNum
                    accBDen += cm.bDen
                }

                val depthHere = maxChildDepth + 1
                val k = children.size

                // Decision node only if k ≥ 2
                if (k >= 2) {
                    // H in nats; children probability p_i := leaves(child)/leaves(u)
                    var Hn = 0.0
                    for (cm in childM) {
                        val p = cm.leaves.toDouble() / sumLeaves.toDouble()
                        Hn -= p * ln(p) // -Σ p ln p
                    }

                    // Normalized local entropy for S
                    val tildeH = Hn / ln(k.toDouble()) // ∈ [0,1]
                    accSNum += sumLeaves.toDouble() * tildeH
                    accSDen += sumLeaves.toDouble()

                    // Effective-branch increment for B: e^{H} - 1
                    val bEffMinus1 = exp(Hn) - 1.0
                    accBNum += sumLeaves.toDouble() * bEffMinus1
                    accBDen += sumLeaves.toDouble()
                }

                Metrics(
                    depth = depthHere,
                    leaves = sumLeaves,
                    sNum = accSNum, sDen = accSDen,
                    bNum = accBNum, bDen = accBDen
                )
            }
        }
    }
}

