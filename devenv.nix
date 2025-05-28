{ pkgs, lib, config, ... }:

{
  packages = [
  ];

  git-hooks.hooks = {};

  languages.python = {
    enable = true;
    uv = {
      enable = true;
    };
  };

  processes.mcp.exec = "uv run fastapi dev src/nutrition_coach/api_server.py --port 5000";
}
