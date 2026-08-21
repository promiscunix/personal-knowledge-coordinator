{ self, inputs }:
{ config, lib, pkgs, ... }:
let
  cfg = config.services.personal-knowledge-coordinator;
  roles = [ "coordinator" "librarian" "researcher" "developer" "reviewer" ];
in
{
  imports = [ inputs.hermes-agent.nixosModules.default ];

  options.services.personal-knowledge-coordinator = {
    enable = lib.mkEnableOption "Hermes-centered personal knowledge coordinator stack";
    stateDir = lib.mkOption {
      type = lib.types.str;
      default = "/srv/personal-knowledge-coordinator";
      description = "Persistent state root for knowledge DB, raw archive, exports, and Hermes state.";
    };
    databaseName = lib.mkOption { type = lib.types.str; default = "pkc"; };
    databaseUser = lib.mkOption { type = lib.types.str; default = "pkc"; };
    listenHost = lib.mkOption { type = lib.types.str; default = "127.0.0.1"; };
    listenPort = lib.mkOption { type = lib.types.port; default = 8765; };
    hermesModel = lib.mkOption { type = lib.types.str; default = "gpt-5.5"; };
    hermesProvider = lib.mkOption { type = lib.types.str; default = "openai-codex"; };
    secretsFile = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "Optional EnvironmentFile containing Hermes/API secrets. Do not commit it.";
    };
  };

  config = lib.mkIf cfg.enable {
    users.groups.pkc = { };
    users.groups.hermes-agents = { };
    users.users = {
      pkc = {
        isSystemUser = true;
        group = "pkc";
        home = cfg.stateDir;
        createHome = true;
        description = "Personal Knowledge Coordinator service user";
      };
    } // lib.genAttrs roles (role: {
      isSystemUser = true;
      group = "hermes-agents";
      home = "${cfg.stateDir}/agents/${role}";
      createHome = true;
      description = "Hermes ${role} role account";
    });

    systemd.tmpfiles.rules = [
      "d ${cfg.stateDir} 0750 pkc hermes-agents -"
      "d ${cfg.stateDir}/archive 0750 pkc pkc -"
      "d ${cfg.stateDir}/exports 0750 pkc pkc -"
      "d ${cfg.stateDir}/backups 0750 pkc pkc -"
      "d ${cfg.stateDir}/backups/postgresql 0750 postgres postgres -"
      "d ${cfg.stateDir}/hermes 0750 coordinator hermes-agents -"
      "z ${cfg.stateDir}/hermes 0750 coordinator hermes-agents -"
      "d ${cfg.stateDir}/hermes/.hermes 0750 coordinator hermes-agents -"
      "z ${cfg.stateDir}/hermes/.hermes 0750 coordinator hermes-agents -"
      "d ${cfg.stateDir}/workspace 0750 coordinator hermes-agents -"
      "z ${cfg.stateDir}/workspace 0750 coordinator hermes-agents -"
      "d ${cfg.stateDir}/agents 0750 root hermes-agents -"
    ] ++ map (role: "d ${cfg.stateDir}/agents/${role} 0750 ${role} hermes-agents -") roles;

    services.postgresql = {
      enable = true;
      package = pkgs.postgresql_16;
      ensureDatabases = [ cfg.databaseName ];
      ensureUsers = [
        {
          name = cfg.databaseUser;
          ensureDBOwnership = true;
        }
      ];
    };

    services.postgresqlBackup = {
      enable = true;
      databases = [ cfg.databaseName ];
      location = "${cfg.stateDir}/backups/postgresql";
      startAt = "03:15:00";
    };

    systemd.services.pkc-schema = {
      description = "Initialize Personal Knowledge Coordinator database schema";
      wantedBy = [ "multi-user.target" ];
      after = [ "postgresql.service" ];
      requires = [ "postgresql.service" ];
      serviceConfig = {
        Type = "oneshot";
        User = cfg.databaseUser;
        Group = "pkc";
        Environment = "PKC_DATABASE_URL=postgresql:///${cfg.databaseName}";
        ExecStart = "${self.packages.${pkgs.system}.pkc-cli}/bin/pkc init-db";
      };
    };

    systemd.services.pkc-api = {
      description = "Personal Knowledge Coordinator capture/search API";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" "postgresql.service" "pkc-schema.service" ];
      requires = [ "postgresql.service" ];
      serviceConfig = {
        User = "pkc";
        Group = "pkc";
        WorkingDirectory = cfg.stateDir;
        Environment = [
          "PKC_DATABASE_URL=postgresql:///${cfg.databaseName}"
          "PKC_HOST=${cfg.listenHost}"
          "PKC_PORT=${toString cfg.listenPort}"
        ];
        ExecStart = "${self.packages.${pkgs.system}.pkc-server}/bin/pkc-server";
        Restart = "always";
        RestartSec = 5;
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.stateDir ];
      };
    };

    services.hermes-agent = {
      enable = true;
      user = "coordinator";
      group = "hermes-agents";
      createUser = false;
      stateDir = "${cfg.stateDir}/hermes";
      workingDirectory = "${cfg.stateDir}/workspace";
      addToSystemPackages = true;
      extraDependencyGroups = [ "messaging" ];
      environmentFiles = lib.optional (cfg.secretsFile != null) cfg.secretsFile;
      settings = {
        model = {
          default = cfg.hermesModel;
          provider = cfg.hermesProvider;
        };
        telegram = {
          allow_from = [ "8028674484" ];
        };
        terminal = {
          backend = "local";
          timeout = 180;
          cwd = "${cfg.stateDir}/workspace";
        };
        compression = {
          enabled = true;
          threshold = 0.85;
        };
        delegation.max_concurrent_children = 3;
        kanban.dispatch_in_gateway = true;
        toolsets = [
          "terminal"
          "file"
          "code_execution"
          "skills"
          "memory"
          "session_search"
          "cronjob"
          "delegation"
          "todo"
          "clarify"
          "kanban"
        ];
      };
      documents = {
        "USER.md" = ''
          # User Profile

          Dale Appleby needs one coordinator agent for capture-first personal knowledge,
          task routing, reminders, project context, management notes, research, and
          durable multi-agent coordination.
        '';
        "MEMORY.md" = ''
          # Operating Memory

          This is the central Hermes environment. Persistent storage, not the model
          context window, is memory. Preserve raw captures and provenance. Retrieve
          only scoped, relevant context. Do not expose management-private records to
          unrelated specialist agents.
        '';
      };
      extraPackages = with pkgs; [ git curl jq ripgrep fd bat eza postgresql_16 sqlite ];
      restart = "always";
      restartSec = 5;
    };

    system.activationScripts.pkc-hermes-profiles = ''
            set -eu
            HERMES_HOME=${lib.escapeShellArg "${cfg.stateDir}/hermes/.hermes"}
            install -d -m 0750 -o coordinator -g hermes-agents "$HERMES_HOME/profiles"
            ${lib.concatMapStringsSep "\n" (role: ''
              install -d -m 0750 -o ${role} -g hermes-agents "$HERMES_HOME/profiles/${role}"
              cat > "$HERMES_HOME/profiles/${role}/SOUL.md" <<'EOF'
      # ${role}

      Role account for the Personal Knowledge Coordinator system. Follow the scope and approval boundaries documented in the repository. Use persistent task/knowledge records rather than treating chat context as memory.
      EOF
              chown ${role}:hermes-agents "$HERMES_HOME/profiles/${role}/SOUL.md"
            '') roles}
    '';

    environment.systemPackages = [ self.packages.${pkgs.system}.pkc-cli pkgs.git pkgs.curl pkgs.jq ];
  };
}
