{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.nodejs_20
    pkgs.nodePackages.pnpm
    pkgs.supabase-cli
  ];

  env = {};

  idx = {
    extensions = [
      "ms-python.python"
      "dbaeumer.vscode-eslint"
      "bradlc.vscode-tailwindcss"
    ];

    workspace = {
      onCreate = {
        install = "pnpm install";
        pip-install-api = "cd packages/api && pip install -r requirements.txt";
        pip-install-core = "cd packages/core && pip install -r requirements.txt";
      };
    };

    previews = {
      enable = true;
      previews = {
        web = {
          command = ["pnpm" "--filter" "web" "dev" "--port" "$PORT"];
          manager = "web";
        };
        api = {
          command = ["uvicorn" "packages.api.main:app" "--reload" "--port" "$PORT"];
          manager = "web";
        };
      };
    };
  };
}
