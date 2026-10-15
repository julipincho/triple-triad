"""Publica SOLO la seleccion revisada; nunca sobrescribe los originales."""
import json
import shutil

from producir_pixel_anime import BASE, LOTE, inventario, sha, verificar

REVISION = {
    "apagon", "asalto_amanecer", "asalto_noche", "camino_lluvia",
    "campamento_tormenta", "escenario_lleno", "escenario_vacio",
}
NUEVO = {
    "ceniza", "campamento_niebla", "campamento_asedio", "trono_derrumbe",
    "trono_nieve", "umbral", "umbral_ancho", "umbral_angosto",
    "umbral_cerrando", "umbral_deslumbrante",
}
RESERVADOS = {"salon", "trono", "trono_guardia"}


def publicar():
    verificar()
    seleccion = {}
    for item in inventario():
        name = item["id"]
        if name in RESERVADOS:
            continue
        origen = "nuevo" if name in NUEVO else "revision" if name in REVISION else "candidatos"
        src = LOTE / origen / item["source"]
        if item["source"].startswith("fondos/"):
            folder, tipo = "cinematicas", "fondo"
        else:
            folder, tipo = ("avatares" if item["tipo"] == "avatar" else "encuentros"), "retrato"
        dst = BASE / "assets" / "pixel_anime" / folder / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        receta = json.loads(src.with_suffix(".json").read_text())
        seleccion["assets/" + item["source"]] = dict(
            tipo=tipo, ruta=dst.relative_to(BASE).as_posix(), sha256=sha(dst),
            original_sha256=sha(LOTE / "originales" / item["source"]),
            modelo=receta["workflow"]["1"]["inputs"]["ckpt_name"],
            seed=receta["seed"], receta=str(src.with_suffix(".json")))
    manifest = dict(lote="pixel_anime_20261013", seleccion=seleccion,
                    reservados={"salon": "Lotes HD aprobados tienen prioridad",
                                "trono": "Sala del trono aprobada tiene prioridad",
                                "trono_guardia": "Candidatos sin guardias legibles: conservar original"})
    (BASE / "assets/pixel_anime/manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    verificar()
    print(f"Publicados {len(seleccion)} assets. Originales, cartas y lotes aprobados intactos.")


if __name__ == "__main__":
    publicar()
