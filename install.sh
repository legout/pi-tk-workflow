#!/usr/bin/env bash
set -euo pipefail

# Repository location for remote installs
REPO_URL="https://raw.githubusercontent.com/legout/pi-tickerflow/main"

# Detect if script is being piped (not run from a local file)
is_piped() {
  # If BASH_SOURCE[0] is not a regular file, we're likely being piped
  [[ ! -f "${BASH_SOURCE[0]:-}" ]] || [[ -p /dev/stdin ]]
}

usage() {
  cat <<'EOF'
Usage:
  # Local install (from cloned repo)
  ./install.sh --global
  ./install.sh --project /path/to/project

  # Remote install (via curl)
  curl -fsSL https://raw.githubusercontent.com/legout/pi-tickerflow/main/install.sh | bash -s -- --global
  curl -fsSL https://raw.githubusercontent.com/legout/pi-tickerflow/main/install.sh | bash -s -- --project /path/to/project

Options:
  --global              Install into ~/.pi/agent and ~/.local/bin/tf
  --project <path>      Install into <path>/.pi (defaults to current dir)
  --remote              Force remote mode (download from GitHub)
  --help                Show this help

Notes:
  This script installs agents, skills, prompts, workflow config, and the tf CLI.
  After install, use 'tf setup' (global) or './.pi/bin/tf setup' (project) for interactive setup.
EOF
}

log() {
  echo "[tf-install] $*" >&2
}

download_file() {
  local url="$1"
  local output="$2"
  local dir
  dir="$(dirname "$output")"

  if ! mkdir -p "$dir" 2>/dev/null; then
    log "ERROR: Cannot create directory $dir (permission denied?)"
    return 1
  fi

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$output" 2>/dev/null
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$url" -O "$output" 2>/dev/null
  else
    log "ERROR: curl or wget required"
    return 1
  fi
}

# Install the CLI binary
install_cli() {
  local source_file="$1"
  local target_dir="$2"
  local is_global="$3"

  # Make CLI executable
  chmod +x "$source_file"

  if [ "$is_global" = true ]; then
    # Global install: try to install to ~/.local/bin/tf
    local global_bin="${HOME}/.local/bin/tf"

    # Create ~/.local/bin if needed
    if ! mkdir -p "${HOME}/.local/bin" 2>/dev/null; then
      log "WARNING: Cannot create ${HOME}/.local/bin"
      log "          Installing CLI to $target_dir/bin/tf instead"
      cp "$source_file" "$target_dir/bin/tf"
      return 1
    fi

    # Copy CLI to ~/.local/bin/tf
    if cp "$source_file" "$global_bin" 2>/dev/null; then
      log "Installed CLI to: $global_bin"

      # Check if ~/.local/bin is in PATH
      if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
        echo ""
        echo "WARNING: ${HOME}/.local/bin is not in your PATH"
        echo "Add this to your shell profile (.bashrc, .zshrc, etc.):"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
      fi
      return 0
    else
      log "WARNING: Cannot install to $global_bin (permission denied?)"
      log "          Installing CLI to $target_dir/bin/tf instead"
      mkdir -p "$target_dir/bin"
      cp "$source_file" "$target_dir/bin/tf"
      return 1
    fi
  else
    # Project install: install to .pi/bin/tf
    mkdir -p "$target_dir/bin"
    cp "$source_file" "$target_dir/bin/tf"
    log "Installed CLI to: $target_dir/bin/tf"
    return 0
  fi
}

# Remote install: download all files from GitHub
install_remote() {
  local target_base="$1"
  local is_global="$2"
  local temp_dir
  temp_dir="$(mktemp -d)"

  log "Downloading from $REPO_URL ..."

  # Download manifest
  local manifest_url="$REPO_URL/config/install-manifest.txt"
  local manifest_file="$temp_dir/install-manifest.txt"

  if ! download_file "$manifest_url" "$manifest_file"; then
    log "ERROR: Failed to download install manifest"
    rm -rf "$temp_dir"
    exit 1
  fi

  # Download CLI first
  local cli_url="$REPO_URL/bin/tf"
  local cli_temp="$temp_dir/tf-cli"

  if download_file "$cli_url" "$cli_temp"; then
    install_cli "$cli_temp" "$target_base" "$is_global"
  else
    log "WARNING: Failed to download CLI"
  fi

  # Download each file in manifest
  local count=0
  local errors=0
  while IFS= read -r line || [ -n "$line" ]; do
    line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
      continue
    fi

    # Skip CLI (already handled)
    if [[ "$line" == "bin/tf" ]]; then
      count=$((count + 1))
      continue
    fi

    local file_url="$REPO_URL/$line"
    local output_file="$target_base/$line"

    if download_file "$file_url" "$output_file"; then
      count=$((count + 1))
    else
      log "WARNING: Failed to download $line"
      errors=$((errors + 1))
    fi
  done < "$manifest_file"

  rm -rf "$temp_dir"

  if [ "$errors" -gt 0 ]; then
    log "WARNING: $errors files failed to download"
  fi

  if [ "$count" -eq 0 ]; then
    log "ERROR: No files were installed"
    exit 1
  fi

  log "Installed $count files to: $target_base"
}

# Local install: copy files from repo
install_local() {
  local target_base="$1"
  local is_global="$2"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  local manifest="$script_dir/config/install-manifest.txt"

  if [ ! -f "$manifest" ]; then
    log "ERROR: Install manifest not found: $manifest"
    exit 1
  fi

  # Install CLI first
  if [ -f "$script_dir/bin/tf" ]; then
    install_cli "$script_dir/bin/tf" "$target_base" "$is_global"
  fi

  local agents_count=0
  local skills_count=0
  local prompts_count=0
  local workflows_count=0

  while IFS= read -r line || [ -n "$line" ]; do
    line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
      continue
    fi

    # Skip CLI (already handled)
    if [[ "$line" == "bin/tf" ]]; then
      continue
    fi

    if [ ! -f "$script_dir/$line" ]; then
      log "WARNING: Missing file: $script_dir/$line"
      continue
    fi
    mkdir -p "$target_base/$(dirname "$line")"
    cp "$script_dir/$line" "$target_base/$line"
    case "$line" in
      agents/*) agents_count=$((agents_count + 1)) ;;
      skills/*) skills_count=$((skills_count + 1)) ;;
      prompts/*) prompts_count=$((prompts_count + 1)) ;;
      workflows/*) workflows_count=$((workflows_count + 1)) ;;
    esac
  done < "$manifest"

  # Create root AGENTS.md for project installs
  if [ -f "$script_dir/docs/AGENTS.md.template" ] && [ ! -f "AGENTS.md" ]; then
    if [ "$is_global" = false ]; then
      cp "$script_dir/docs/AGENTS.md.template" "AGENTS.md"
      log "Created AGENTS.md in project root"
    fi
  fi

  echo ""
  echo "Installed IRF workflow files to: $target_base"
  echo ""
  echo "Installed components:"
  echo "  - tf CLI (command-line tool)"
  echo "  - $agents_count agents (execution units)"
  echo "  - $skills_count skills (domain expertise)"
  echo "  - $prompts_count prompts (command entry points)"
  echo "  - $workflows_count workflow files"
}

# Main
main() {
  local target_base=""
  local is_global=false
  local use_remote=false

  # Check if being piped
  if is_piped; then
    use_remote=true
  fi

  # Parse arguments
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --global)
        target_base="$HOME/.pi/agent"
        is_global=true
        shift
        ;;
      --project)
        if [ -z "${2:-}" ]; then
          log "ERROR: Missing path after --project"
          exit 1
        fi
        target_base="$2/.pi"
        is_global=false
        shift 2
        ;;
      --remote)
        use_remote=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        log "ERROR: Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done

  # Default for project install if --project not specified
  if [ -z "$target_base" ]; then
    # If not global, default to current directory
    target_base="$(pwd)/.pi"
    is_global=false
  fi

  # Create target directory
  if ! mkdir -p "$target_base" 2>/dev/null; then
    log "ERROR: Cannot create $target_base (permission denied?)"
    log "Try: sudo curl ... | bash -s -- --global"
    exit 1
  fi

  # Install
  if [ "$use_remote" = true ]; then
    install_remote "$target_base" "$is_global"
    echo ""
    if [ "$is_global" = true ]; then
      echo "Next steps:"
      echo "  1. Ensure ~/.local/bin is in your PATH:"
      echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
      echo "  2. Install required Pi extensions:"
      echo "     pi install npm:pi-prompt-template-model"
      echo "     pi install npm:pi-model-switch"
      echo "     pi install npm:pi-subagents"
      echo "  3. Run interactive setup:"
      echo "     tf setup"
      echo "  4. Sync configuration:"
      echo "     tf sync"
      echo "  5. Initialize Ralph:"
      echo "     tf ralph init"
      echo "  6. Start working:"
      echo "     /tf <ticket>"
    else
      echo "Next steps:"
      echo "  1. Install required Pi extensions:"
      echo "     pi install npm:pi-prompt-template-model"
      echo "     pi install npm:pi-model-switch"
      echo "     pi install npm:pi-subagents"
      echo "  2. Run interactive setup:"
      echo "     ./.pi/bin/tf setup"
      echo "  3. Sync configuration:"
      echo "     ./.pi/bin/tf sync"
      echo "  4. Initialize Ralph:"
      echo "     ./.pi/bin/tf ralph init"
      echo "  5. Start working:"
      echo "     /tf <ticket>"
    fi
  else
    install_local "$target_base" "$is_global"
    echo ""
    if [ "$is_global" = true ]; then
      echo "Next steps:"
      echo "  1. Ensure ~/.local/bin is in your PATH:"
      echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
      echo "  2. Run interactive setup:"
      echo "     tf setup"
      echo "  3. Sync configuration:"
      echo "     tf sync"
      echo "  4. Initialize Ralph:"
      echo "     tf ralph init"
      echo "  5. Start working:"
      echo "     /tf <ticket>"
    else
      echo "Next steps:"
      echo "  1. Run interactive setup:"
      echo "     ./.pi/bin/tf setup"
      echo "  2. Sync configuration:"
      echo "     ./.pi/bin/tf sync"
      echo "  3. Review AGENTS.md (project patterns)"
      echo "  4. Initialize Ralph:"
      echo "     ./.pi/bin/tf ralph init"
      echo "  5. Start working:"
      echo "     /tf <ticket>"
    fi
  fi
}

main "$@"
