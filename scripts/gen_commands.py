"""Génère `commande.json` : liste de toutes les commandes du bot.

Pour chaque commande (sous-commandes incluses) : nom, courte description,
catégorie, permission requise, arguments (nom + obligatoire/facultatif +
valeur par défaut) et alias éventuels. Descriptions issues du catalogue i18n
(français par défaut), avec repli sur la description du décorateur.

Usage :  python -m scripts.gen_commands
"""
import asyncio
import json
from pathlib import Path

import config
from bot import Watcher
from utils import categories as cats
from utils.i18n import t

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "commande.json"

OWNER_CATEGORY = "👑 Owner du bot"


def _is_owner(command) -> bool:
    return bool(command.module and command.module.startswith("cogs.owner"))


def _describe(command) -> str:
    """Description traduite (cmddesc.<nom>) avec repli sur le décorateur."""
    key = f"cmddesc.{command.qualified_name}"
    translated = t(None, key)
    if translated != key:
        return translated
    return command.description or command.help or ""


def _arguments(command) -> list[dict]:
    args = []
    for name, param in command.clean_params.items():
        entry = {"nom": name, "obligatoire": bool(param.required)}
        if not param.required and param.default not in (None, param.empty, ""):
            entry["defaut"] = param.default
        args.append(entry)
    return args


def _command_entry(command) -> dict:
    owner = _is_owner(command)
    cat_key, perm_key = cats.category_of(command)
    entry = {
        "nom": command.qualified_name,
        "description": _describe(command),
        "categorie": OWNER_CATEGORY if owner else t(None, cat_key),
        "permission": (
            t(None, perm_key) if perm_key
            else ("Owner du bot" if owner else "Aucune")
        ),
        "arguments": _arguments(command),
    }
    if command.aliases:
        entry["alias"] = list(command.aliases)
    return entry


async def main() -> None:
    bot = Watcher()
    await bot._load_cogs()

    commands_all = sorted(bot.walk_commands(), key=lambda c: c.qualified_name)
    data = {
        "bot": "Watcher",
        "version": config.VERSION,
        "prefixe_defaut": config.PREFIX,
        "total": len(commands_all),
        "commandes": [_command_entry(c) for c in commands_all],
    }
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    await bot.close()
    print(f"commande.json généré : {len(commands_all)} commandes.")


if __name__ == "__main__":
    asyncio.run(main())
