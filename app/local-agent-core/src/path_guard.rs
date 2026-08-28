//! Guarda de caminhos do corpo local — espelho fiel de
//! `backend/permissions/path_guard.py` (8.0 · B.2).
//!
//! O corpo só lê/escreve DENTRO de pastas que o dono autorizou (whitelist).
//! Sobre isso há uma **blacklist dura** (raiz do SO, credenciais) que é recusada
//! MESMO que o dono tente autorizar. Todo caminho é normalizado (expande `~`,
//! colapsa `.`/`..`) para impedir escape da whitelist por caminho relativo.

use std::path::{Component, Path, PathBuf};

/// Blacklist DURA — nunca liberável (§B.2/B.10). Mesma lista do Python.
const BLACKLIST: &[&str] = &[
    "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/boot", "/dev", "/proc",
    "/sys", "/root", "/var/lib", "/System", "/Library",
    "C:\\Windows", "C:\\Windows\\System32", "C:\\Program Files",
];
/// Nomes/sufixos sensíveis recusados em qualquer lugar (credenciais/chaves).
const SENSITIVE: &[&str] = &[
    ".ssh", ".gnupg", ".aws", ".config/gcloud", "keychain", "id_rsa",
    "id_ed25519", ".env", "shadow", "sam",
];

/// Expande `~`/`~/...` usando HOME (espelha `os.path.expanduser`).
fn expanduser(path: &str) -> String {
    if path == "~" {
        std::env::var("HOME").unwrap_or_else(|_| "~".to_string())
    } else if let Some(rest) = path.strip_prefix("~/") {
        match std::env::var("HOME") {
            Ok(h) => format!("{}/{}", h.trim_end_matches('/'), rest),
            Err(_) => path.to_string(),
        }
    } else {
        path.to_string()
    }
}

/// Normaliza (absoluto + colapsa `.`/`..` lexicamente). Não toca no disco,
/// então funciona mesmo para caminhos inexistentes (como `resolve(strict=False)`).
pub fn norm(path: &str) -> String {
    let expanded = expanduser(path);
    let base = if Path::new(&expanded).is_absolute() {
        PathBuf::from(&expanded)
    } else {
        std::env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("/"))
            .join(&expanded)
    };
    let mut out = PathBuf::new();
    for comp in base.components() {
        match comp {
            Component::ParentDir => {
                out.pop();
            }
            Component::CurDir => {}
            other => out.push(other.as_os_str()),
        }
    }
    out.to_string_lossy().to_string()
}

/// Caminho crítico (raiz do SO, credenciais)? Recusado sempre.
pub fn is_blacklisted(path: &str) -> bool {
    let low = norm(path).to_lowercase();
    for bad in BLACKLIST {
        let b = norm(bad).to_lowercase();
        if low == b || low.starts_with(&format!("{b}/")) {
            return true;
        }
    }
    SENSITIVE.iter().any(|tok| low.contains(tok))
}

/// Whitelist de pastas autorizadas + blacklist imutável.
#[derive(Debug, Default, Clone)]
pub struct PathGuard {
    allowed: Vec<String>,
}

impl PathGuard {
    pub fn new() -> Self {
        Self { allowed: Vec::new() }
    }

    /// Autoriza uma pasta — a menos que esteja na blacklist dura.
    pub fn allow(&mut self, path: &str) -> bool {
        if is_blacklisted(path) {
            return false; // recusa MESMO com o dono pedindo
        }
        let p = norm(path);
        if !self.allowed.contains(&p) {
            self.allowed.push(p);
        }
        true
    }

    /// Caminho está dentro de alguma pasta autorizada e fora da blacklist?
    pub fn is_allowed(&self, path: &str) -> bool {
        if is_blacklisted(path) {
            return false;
        }
        let p = norm(path);
        self.allowed
            .iter()
            .any(|base| p == *base || p.starts_with(&format!("{base}/")))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn blacklist_recusa_raiz_do_so() {
        assert!(is_blacklisted("/etc/passwd"));
        assert!(is_blacklisted("/root/segredo"));
        assert!(is_blacklisted("/etc"));
    }

    #[test]
    fn blacklist_recusa_credenciais_em_qualquer_lugar() {
        assert!(is_blacklisted("/home/dono/.ssh/id_rsa"));
        assert!(is_blacklisted("/home/dono/projeto/.env"));
    }

    #[test]
    fn whitelist_permite_dentro_recusa_fora() {
        let mut g = PathGuard::new();
        assert!(g.allow("/home/dono/Documentos"));
        assert!(g.is_allowed("/home/dono/Documentos/nota.txt"));
        assert!(!g.is_allowed("/home/dono/Outro/nota.txt"));
    }

    #[test]
    fn escape_por_dotdot_e_bloqueado() {
        let mut g = PathGuard::new();
        g.allow("/home/dono/Documentos");
        // /home/dono/Documentos/../../.ssh/id_rsa → /home/dono/.ssh/id_rsa
        assert!(!g.is_allowed("/home/dono/Documentos/../../.ssh/id_rsa"));
    }

    #[test]
    fn blacklist_nunca_liberavel_nem_pedindo() {
        let mut g = PathGuard::new();
        assert!(!g.allow("/etc")); // recusa a própria autorização
        assert!(!g.is_allowed("/etc/hosts"));
    }
}
