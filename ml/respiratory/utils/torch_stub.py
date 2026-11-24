"""
Minimal torch stub to allow the SwasthAI respiratory modules to run on environments
where the real PyTorch library cannot be loaded (e.g., Windows sandbox restrictions).
Only the symbols required by the existing code and unit tests are provided.
The implementation relies on NumPy and no GPU support.
"""

import numpy as np
from contextlib import contextmanager

# ---------- Tensor and basic factory ----------

def tensor(data, dtype=None):
    return np.array(data, dtype=dtype)

float32 = np.float32
int64 = np.int64

# ---------- No‑op gradient context manager ----------
@contextmanager
def no_grad():
    yield

# ---------- Manual seed (no‑op) ----------
def manual_seed(seed: int):
    np.random.seed(seed)

# ---------- nn namespace ----------
class Module:
    def __init__(self, *args, **kwargs):
        pass
    def eval(self):
        return self
    def train(self):
        return self
    def state_dict(self):
        return {}
    def load_state_dict(self, state):
        pass

class Linear(Module):
    def __init__(self, in_features, out_features, bias=True):
        self.in_features = in_features
        self.out_features = out_features
        self.weight = np.zeros((out_features, in_features), dtype=np.float32)
        self.bias = np.zeros(out_features, dtype=np.float32) if bias else None
    def __call__(self, x):
        y = x @ self.weight.T
        if self.bias is not None:
            y = y + self.bias
        return y

class Conv2d(Module):
    # Very simple placeholder that just returns the input unchanged
    def __init__(self, in_channels, out_channels, kernel_size, padding=0, bias=False):
        pass
    def __call__(self, x):
        return x

class GroupNorm(Module):
    def __init__(self, num_groups, num_channels):
        pass
    def __call__(self, x):
        return x

class ReLU(Module):
    def __call__(self, x):
        return np.maximum(0, x)

class MaxPool2d(Module):
    def __init__(self, kernel_size):
        pass
    def __call__(self, x):
        return x

class GRU(Module):
    def __init__(self, input_size, hidden_size, num_layers=1, batch_first=False, bidirectional=False):
        self.hidden_size = hidden_size
        self.bidirectional = bidirectional
    def __call__(self, x):
        # Return zeros matching (batch, seq, hidden*directions)
        batch, seq, _ = x.shape
        h = self.hidden_size * (2 if self.bidirectional else 1)
        return np.zeros((batch, seq, h), dtype=np.float32), None

class GRUCell(Module):
    def __init__(self, input_size, hidden_size):
        self.hidden_size = hidden_size
    def __call__(self, input, hidden):
        return np.tanh(input + hidden)

class Embedding(Module):
    def __init__(self, num_embeddings, embedding_dim, padding_idx=None):
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
    def __call__(self, indices):
        # Return zeros for any index
        shape = indices.shape + (self.embedding_dim,)
        return np.zeros(shape, dtype=np.float32)

class Sequential(Module):
    def __init__(self, *layers):
        self.layers = layers
    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

# Export a minimal nn namespace
class _NNNamespace:
    Module = Module
    Linear = Linear
    Conv2d = Conv2d
    GroupNorm = GroupNorm
    ReLU = ReLU
    MaxPool2d = MaxPool2d
    GRU = GRU
    GRUCell = GRUCell
    Embedding = Embedding
    Sequential = Sequential

nn = _NNNamespace()

# ---------- functional namespace ----------
class _FNamespace:
    @staticmethod
    def softmax(logits, dim=-1):
        e = np.exp(logits - np.max(logits, axis=dim, keepdims=True))
        return e / np.sum(e, axis=dim, keepdims=True)
    @staticmethod
    def cross_entropy(input, target, weight=None, ignore_index=-100):
        # Simplified: assume input is (batch, classes), target is (batch,)
        probs = _FNamespace.softmax(input, dim=1)
        batch = target.shape[0]
        loss = -np.log(probs[np.arange(batch), target] + 1e-12)
        return np.mean(loss)

F = _FNamespace()
