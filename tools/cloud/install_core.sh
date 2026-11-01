cd /tmp/code/C500-Comfyui-Package
echo "=== BEFORE: frontend version ==="
python -c "import comfyui_frontend_package as f; print(f.__version__)" 2>&1
echo "=== RUN install_offline.sh (core) ==="
bash scripts/install_offline.sh 2>&1
echo "=== RC=$? ==="