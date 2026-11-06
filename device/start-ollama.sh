#!/bin/bash
# Start the local Ollama server the ATMAN device expects.
# cultivate.py / brain.py auto_backend() pings http://localhost:11434 for qwen2.5:1.5b.
# Keep this server running (or restart it) so scheduled device jobs get the real
# generative backend instead of the SimulatedBackend stub.
export PATH="$HOME/workspace/bin:$PATH"
export OLLAMA_MODELS="$HOME/workspace/atman/models"
export OLLAMA_HOST="127.0.0.1:11434"
exec "$HOME/workspace/bin/ollama" serve
