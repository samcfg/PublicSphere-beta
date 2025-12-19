{
  description = "PublicSphere development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };

      # PostgreSQL with AGE extension enabled
      postgresqlWithAge = pkgs.postgresql_17.withPackages (ps: [ ps.age ]);
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # PostgreSQL with AGE extension
          postgresqlWithAge

          # Python environment
          python311

          # Node.js environment
          nodejs_22
          pnpm

          # Python package manager
          uv

          # Libraries needed by psycopg2-binary
          zlib

          # Utilities
          git
        ];

        shellHook = ''
          echo "PublicSphere Development Environment"
          echo "===================================="
          echo ""
          echo "Available tools:"
          echo "  PostgreSQL: $(postgres --version | head -n1)"
          echo "  Python:     $(python --version)"
          echo "  Node.js:    $(node --version)"
          echo "  pnpm:       $(pnpm --version)"
          echo "  uv:         $(uv --version)"
          echo ""
          echo "PostgreSQL data directory: .postgres-data/"
          echo ""
          echo "Quick start commands:"
          echo "  1. Initialize PostgreSQL (first time only):"
          echo "     initdb -D .postgres-data -U sam --locale=C"
          echo ""
          echo "  2. Start PostgreSQL:"
          echo "     pg_ctl -D .postgres-data -l .postgres-data/logfile start"
          echo ""
          echo "  3. Stop PostgreSQL:"
          echo "     pg_ctl -D .postgres-data stop"
          echo ""
          echo "  4. Backend setup:"
          echo "     cd backend && uv sync && uv run python manage.py migrate"
          echo ""
          echo "  5. Frontend setup:"
          echo "     cd frontend && pnpm install"
          echo ""

          # Set environment variables
          export PGDATA=".postgres-data"
          export PGHOST="localhost"
          export PGPORT="5432"
          export PGUSER="sam"
          export PGDATABASE="postgres"

          # Add library paths for psycopg2-binary
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.zlib ]}:$LD_LIBRARY_PATH"

          # Add project binaries to PATH
          export PATH="$PWD/backend/.venv/bin:$PATH"
        '';
      };
    };
}
