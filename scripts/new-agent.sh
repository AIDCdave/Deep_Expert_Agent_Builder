#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: new-agent <agent_name> <input_file> [targets]"
  echo "Example: new-agent Collins_Ranch_Content_Strategist ./intake.md"
  echo "Example: new-agent Collins_Ranch_Content_Strategist ./intake.md pas,claude,grok"
  echo ""
  echo "Targets: pas, chatgpt-custom-gpt, openai-responses, claude, gemma-4, hermes, grok"
  echo "Default: all"
  exit 1
fi

AGENT_NAME="$1"
INPUT_FILE="$2"
TARGETS="${3:-}"
WORKSPACE_ROOT="$HOME/Deep_Expert_Agent_Builder/workspaces"
AGENT_DIR="$WORKSPACE_ROOT/$AGENT_NAME"

if [ -d "$AGENT_DIR" ]; then
  echo "Workspace already exists: $AGENT_DIR"
  exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "Input file not found: $INPUT_FILE"
  exit 1
fi

mkdir -p "$AGENT_DIR/00_inputs"
cp "$INPUT_FILE" "$AGENT_DIR/00_inputs/"

echo "✓ Created workspace: $AGENT_DIR"
echo "✓ Copied input: $(basename "$INPUT_FILE") → 00_inputs/"

if [ -n "$TARGETS" ]; then
  echo "✓ Targets: $TARGETS"
  echo ""
  echo "  Running pipeline..."
  dea-builder run "$AGENT_DIR" --targets "$TARGETS"
else
  echo "✓ Targets: all"
  echo ""
  echo "  Running pipeline..."
  dea-builder run "$AGENT_DIR"
fi
