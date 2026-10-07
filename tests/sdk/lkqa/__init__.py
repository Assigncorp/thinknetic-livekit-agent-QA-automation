"""
Black-box tests of the deployed agent over the LiveKit SDK.

The judge package owns the transcript schema and the deterministic oracle; this
package owns getting a real call into that schema. `bridge` is the one place the
seam is crossed - see its docstring for why it is crossed at all.
"""
