import math
import unittest
from context_router.embeddings import (
    DeterministicLocalEmbedder,
    tokenize_text,
    pack_vector,
    unpack_vector,
    VECTOR_DIM,
)


class TestEmbeddings(unittest.TestCase):
    def setUp(self):
        self.embedder = DeterministicLocalEmbedder(dimension=VECTOR_DIM)

    def test_tokenize_text(self):
        tokens = tokenize_text("authMiddleware handles JWT verification")
        self.assertIn("auth", tokens)
        self.assertIn("middleware", tokens)
        self.assertIn("jwt", tokens)
        self.assertIn("verification", tokens)

    def test_vector_normalization(self):
        vec = self.embedder.embed_text("Implement auth middleware with JWT tokens", title="Auth Middleware")
        self.assertEqual(len(vec), VECTOR_DIM)
        # Check L2 unit length
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_cosine_similarity(self):
        vec_auth1 = self.embedder.embed_text("Authenticate user with password hash")
        vec_auth2 = self.embedder.embed_text("User authentication and credential check")
        vec_db = self.embedder.embed_text("PostgreSQL connection pooling and SQL schema migrations")

        sim_auth = self.embedder.similarity(vec_auth1, vec_auth2)
        sim_diff = self.embedder.similarity(vec_auth1, vec_db)

        self.assertGreater(sim_auth, sim_diff)
        self.assertGreater(sim_auth, 0.4)

    def test_pack_unpack_vector(self):
        vec = self.embedder.embed_text("Testing vector binary serialization")
        blob = pack_vector(vec)
        self.assertEqual(len(blob), VECTOR_DIM * 4)  # 4 bytes per 32-bit float
        restored = unpack_vector(blob, dim=VECTOR_DIM)
        self.assertEqual(len(restored), VECTOR_DIM)
        for orig, res in zip(vec, restored):
            self.assertAlmostEqual(orig, res, places=5)


if __name__ == "__main__":
    unittest.main()
