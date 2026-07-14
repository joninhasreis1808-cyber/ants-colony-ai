// Ant's — ponto de entrada do app nativo (desktop).
// Em builds mobile, o entrypoint é `ants_lib::run` via mobile_entry_point.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    ants_lib::run();
}
