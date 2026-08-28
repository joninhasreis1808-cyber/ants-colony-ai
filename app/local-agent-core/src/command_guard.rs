//! Guarda de comandos do corpo local — espelho fiel de
//! `backend/action/command_guard.py` (8.0 · B.8 + B.10).
//!
//! Regra: **whitelist explícita, nunca blacklist.** Só comandos aprovados rodam,
//! sempre como lista de argumentos (sem shell interpolado). Bloqueia qualquer
//! escalonamento de privilégio (sudo/runas/pkexec…) e padrões destrutivos —
//! se a colônia "descobrir" um caminho, recusa e reporta.

/// Binários permitidos (leitura/inspeção — nada destrutivo). Igual ao Python.
const WHITELIST: &[&str] = &[
    "echo", "ls", "cat", "pwd", "whoami", "date", "df", "du", "uname",
    "hostname", "python", "python3", "pip", "node", "npm", "git",
];
/// Tokens de escalonamento — recusados SEMPRE (§B.10).
const ESCALATION: &[&str] = &[
    "sudo", "su", "runas", "doas", "pkexec", "chmod", "chown", "setcap",
    "defender", "netsh", "firewall", "gpupdate", "reg", "bcdedit",
];
/// Substrings destrutivas bloqueadas.
const DANGER_SUBSTR: &[&str] = &["rm -rf", "mkfs", "dd if=", ":(){", "format ", "> /dev/sd"];

/// Veredito auditável de um comando (espelha o dict do Python).
#[derive(Debug, Clone)]
pub struct Verdict {
    pub allowed: bool,
    pub argv: Vec<String>,
    pub reason: String,
    pub escalation: bool,
}

/// Divide em argv sem shell (espelha `shlex.split(posix=True)`).
pub fn to_argv(command: &str) -> Vec<String> {
    shlex::split(command).unwrap_or_default()
}

/// Nome do binário: última parte do caminho, minúsculo (POSIX e Windows).
fn binary_name(arg0: &str) -> String {
    arg0.rsplit(['/', '\\']).next().unwrap_or(arg0).to_lowercase()
}

/// Pode rodar? Por quê (não)? Mesma ordem de checagem do Python.
pub fn check(command: &str) -> Verdict {
    let argv = to_argv(command);
    if argv.is_empty() {
        return Verdict {
            allowed: false,
            argv,
            reason: "comando vazio".to_string(),
            escalation: false,
        };
    }
    let raw = argv.join(" ").to_lowercase();
    let binary = binary_name(&argv[0]);

    let words: Vec<&str> = raw.split_whitespace().collect();
    if ESCALATION.iter().any(|t| words.contains(t)) || ESCALATION.contains(&binary.as_str()) {
        return Verdict {
            allowed: false,
            argv,
            reason: "escalonamento de privilégio recusado (B.10)".to_string(),
            escalation: true,
        };
    }
    if DANGER_SUBSTR.iter().any(|sub| raw.contains(sub)) {
        return Verdict {
            allowed: false,
            argv,
            reason: "padrão destrutivo bloqueado".to_string(),
            escalation: false,
        };
    }
    if !WHITELIST.contains(&binary.as_str()) {
        return Verdict {
            allowed: false,
            argv,
            reason: format!("binário '{binary}' fora da whitelist"),
            escalation: false,
        };
    }
    Verdict {
        allowed: true,
        argv,
        reason: "na whitelist".to_string(),
        escalation: false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn whitelist_permite_leitura() {
        let v = check("echo ola colonia");
        assert!(v.allowed);
        assert_eq!(v.argv, vec!["echo", "ola", "colonia"]);
    }

    #[test]
    fn sudo_e_recusado_como_escalonamento() {
        let v = check("sudo rm -rf /");
        assert!(!v.allowed);
        assert!(v.escalation);
    }

    #[test]
    fn rm_rf_e_padrao_destrutivo() {
        // git está na whitelist, mas "rm -rf" é substring destrutiva.
        let v = check("git rm -rf .");
        assert!(!v.allowed);
    }

    #[test]
    fn binario_fora_da_whitelist_recusado() {
        let v = check("curl http://malicioso");
        assert!(!v.allowed);
        assert!(v.reason.contains("fora da whitelist"));
    }

    #[test]
    fn comando_vazio_recusado() {
        assert!(!check("").allowed);
    }
}
