# obsidian-wiki

This is the repository-owned, standard-library-only deterministic CLI used by the Managed
Wiki Skills. It is released with MySkills, not from PyPI.

Offline/local installation into the private installer-managed virtual environment:

```powershell
& $python -m pip install --no-deps --no-build-isolation <MySkills>\tools\obsidian-wiki
```

Both interfaces are supported:

```powershell
obsidian-wiki --version
python -m obsidian_wiki --version
```
