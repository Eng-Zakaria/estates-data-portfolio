# Minimal tflint config (P05): built-in rules only, no remote plugins so
# `tflint --init` works offline-safe on CI.
config {
  call_module_type = "local"
}
