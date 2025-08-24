#!/bin/bash
# Installation script for router_controller

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
SCRIPT_NAME="router_controller"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy the script
print_status "Installing $SCRIPT_NAME to $INSTALL_DIR..."
cp "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    print_warning "~/.local/bin is not in your PATH"
    print_status "Add this line to your ~/.zshrc or ~/.bash_profile:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    print_status "Then run: source ~/.zshrc  (or restart your terminal)"
else
    print_status "✅ Installation complete!"
    print_status "You can now run: router_controller --help"
fi

print_status ""
print_status "Usage examples:"
echo "  router_controller status              # Check radio status"
echo "  router_controller on                  # Turn radio on"
echo "  router_controller off                 # Turn radio off"
echo "  router_controller on --debug          # Turn on with debug mode"