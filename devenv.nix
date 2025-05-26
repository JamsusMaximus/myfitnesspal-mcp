{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

let
  python-packages =
    p: with p; [
      pip
      python-lsp-server
      epc
      pylint
    ];
in
{
  name = "nutrition-coach";
  # https://devenv.sh/basics/
  env = {
    GREET = "🛠️ Let's hack ";
  };

  # https://devenv.sh/scripts/
  scripts = {
    hello.exec = "echo $GREET";
    cat.exec = "bat $@";
    check-inception-updates.exec = ''
      GREEN="\033[0;32m";
      NC="\033[0m";

      latest_tag=$(curl -s -L -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/repos/DataChefHQ/inception/releases/latest | jq --raw-output '.tag_name')
      current_commit=$(yq '.["_commit"]' .copier-answers.yml)

      if [[ "$(printf '%s\n' "$current_commit" "$latest_tag" | sort -V | head -n 1)" != "$latest_tag" ]]; then
        echo
        echo "🎉 There's an update available for Inception!"
        echo
        echo -e "    Your version:  $current_commit"
        echo -e "  Latest version:  $latest_tag"
        echo
        echo -e To update, run "$GREEN"inception-update"$NC" in your shell.
        echo
        echo "⚠️ WARNING"
        echo
        echo "  Sometimes it's impossible to know what to do with a diff code hunk."
        echo "  In that case, the conflicting file is updated with conflict markers,"
        echo "  and you'll have to choose which version to keep."
        echo
        echo "  More info at: https://copier.readthedocs.io/en/stable/updating/"
      fi
    '';

    inception-update = {
      description = "Sync this project with the latest version of Inception.";
      exec = "pipx run copier update --defaults -T --trust";
    };

    show = {
      # Prints scripts that have a description
      # Adapted from https://github.com/cachix/devenv/blob/ef61728d91ad5eb91f86cdbcc16070602e7afa16/examples/scripts/devenv.nix#L34
      exec = ''
        GREEN="\033[0;32m";
        YELLOW="\033[33m";
        NC="\033[0m";
        echo
        echo -e "✨ Helper scripts you can run to make your development richer:"
        echo
        ${pkgs.gnused}/bin/sed -e 's| |••|g' -e 's|=| |' <<EOF | ${pkgs.util-linuxMinimal}/bin/column -t | ${pkgs.gnused}/bin/sed -e "s|^\([^ ]*\)|$(printf "$GREEN")\1$(printf "$NC"):    |" -e "s|^|$(printf "$YELLOW*$NC") |" -e 's|••| |g'
        ${lib.generators.toKeyValue { } (
          lib.mapAttrs (name: value: value.description) (
            lib.filterAttrs (_: value: value.description != "") config.scripts
          )
        )}
        EOF
        echo
      '';
      description = "Print this message and exit.";
    };

    release = {
      # This script is temporary due to two problems:
      #  1. `cz` requires a personal github token to publish a release https://commitizen-tools.github.io/commitizen/tutorials/github_actions/
      #  2. `cz bump` fails to sign in a terminal: https://github.com/commitizen-tools/commitizen/issues/1184
      exec = ''
        rm CHANGELOG.md
        cz bump --files-only --check-consistency
        git tag $(python -c "from src.nutrition_coach import __version__; print(__version__)")
      '';
      description = "Release a new version and update the CHANGELOG.";
    };

    pyfix = {
      exec = "ruff check . --fix && ruff format .";
      description = "Lint, (possibly) fix and apply formatting to python files.";
    };
  };

  # https://devenv.sh/packages/
  packages = with pkgs; [
    nixfmt-rfc-style
    bat
    jq
    yq-go
    tealdeer
    pipx # to use copier in projects
    stdenv.cc.cc.lib # required by jupyter
    gcc-unwrapped # fix: libstdc++.so.6: cannot open shared object file
    libz # fix: for numpy/pandas import
    (python3.withPackages python-packages)
  ];

  languages = {
    python = {
      enable = true;
      poetry = {
        enable = true;
        activate.enable = true;
        install.enable = true;
        install.allExtras = true;
        install.groups = [ "dev" ];
      };
    };
  };

  enterShell = ''
    hello
    show
    check-inception-updates
  '';

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.hooks = {
    nixfmt-rfc-style = {
      enable = true;
      excludes = [ ".devenv.flake.nix" ];
    };
    yamllint = {
      enable = true;
      settings.preset = "relaxed";
    };
    check-merge-conflicts.enable = true;
    ruff.enable = true;
    editorconfig-checker.enable = true;
  };

  # Make diffs fantastic
  difftastic.enable = true;

  # https://devenv.sh/integrations/dotenv/
  dotenv.enable = true;

  # https://devenv.sh/integrations/codespaces-devcontainer/
  devcontainer.enable = true;
}
