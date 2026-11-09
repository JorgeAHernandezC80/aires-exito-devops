#!/usr/bin/env bash
# Publica este repositorio en GitHub, activa GitHub Pages y abre los pull requests pendientes.
#
# Requisitos: git y GitHub CLI (https://cli.github.com) con sesión iniciada: `gh auth login`.
# En Windows ejecutarlo desde Git Bash.
#
#   bash scripts/publicar_en_github.sh               # crea repo, sube main y abre los 2 PRs
#   bash scripts/publicar_en_github.sh --fusionar    # además espera el CI y fusiona los PRs
#
set -euo pipefail

REPO_NOMBRE="${REPO_NOMBRE:-aires-exito-devops}"
RAMAS_PR=("docs/readme-flujo-devops" "feature/actualizacion-programada")
FUSIONAR=false
[[ "${1:-}" == "--fusionar" ]] && FUSIONAR=true

cd "$(git rev-parse --show-toplevel)"

echo "==> Verificando GitHub CLI"
gh auth status >/dev/null 2>&1 || { echo "Primero ejecuta: gh auth login"; exit 1; }
DUENO="$(gh api user --jq .login)"
REPO="$DUENO/$REPO_NOMBRE"
echo "    Cuenta: $DUENO  ->  repositorio: $REPO"

echo "==> Creando el repositorio (si no existe)"
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "    Ya existe, se reutiliza."
else
  gh repo create "$REPO" --public \
    --description "Web scraping de aires acondicionados en Éxito.com con CI/CD (IU Digital)"
fi
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$REPO.git"

echo "==> Activando GitHub Pages con GitHub Actions como fuente"
gh api -X POST "repos/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
  || gh api -X PUT "repos/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
  || echo "    (Actívalo a mano: Settings > Pages > Source: GitHub Actions)"

echo "==> Permitiendo que Actions abra pull requests (workflow semanal)"
gh api -X PUT "repos/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true >/dev/null 2>&1 \
  || echo "    (Opcional, a mano: Settings > Actions > General > Workflow permissions)"

echo "==> Subiendo main (dispara CI y Deploy)"
git push -u origin main

echo "==> Subiendo ramas y abriendo pull requests"
titulo_de() { git log -1 --format=%s "$1"; }
cuerpo_de() {
  cat <<EOF
## ¿Qué cambia?

$(git log -1 --format=%b "$1")

## ¿Cómo se probó?

- [x] \`ruff check .\` y \`ruff format --check .\`
- [x] \`pytest\` en verde (lo confirma el check **CI** de este PR)
EOF
}
for rama in "${RAMAS_PR[@]}"; do
  git push -u origin "$rama"
  if gh pr view "$rama" --repo "$REPO" >/dev/null 2>&1; then
    echo "    PR de $rama ya existe"
  else
    gh pr create --repo "$REPO" --base main --head "$rama" \
      --title "$(titulo_de "$rama")" --body "$(cuerpo_de "$rama")"
  fi
done

if $FUSIONAR; then
  for rama in "${RAMAS_PR[@]}"; do
    echo "==> Esperando el CI del PR de $rama"
    sleep 10
    gh pr checks "$rama" --repo "$REPO" --watch --fail-fast
    gh pr merge "$rama" --repo "$REPO" --merge --delete-branch
  done
  git switch main && git pull --ff-only origin main
fi

echo
echo "Listo."
echo "  Repositorio:  https://github.com/$REPO"
echo "  Actions:      https://github.com/$REPO/actions"
echo "  Pull requests: https://github.com/$REPO/pulls"
echo "  Reporte (unos minutos después del Deploy): https://$(echo "$DUENO" | tr "[:upper:]" "[:lower:]").github.io/$REPO_NOMBRE/"
