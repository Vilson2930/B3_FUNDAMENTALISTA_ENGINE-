# ============================================================
# cvm_data.py
# B3 FUNDAMENTALISTA ENGINE
# CVM com download + cache local inteligente
# ============================================================

import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

# ============================================================
# CONFIG
# ============================================================

ANO_DFP = 2025
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DOWNLOAD CVM COM CACHE
# ============================================================

def baixar_zip_cvm(ano=ANO_DFP):
    url = (
        f"https://dados.cvm.gov.br/dados/"
        f"CIA_ABERTA/DOC/DFP/DADOS/"
        f"dfp_cia_aberta_{ano}.zip"
    )

    arquivo_cache = CACHE_DIR / f"dfp_cia_aberta_{ano}.zip"

    print("=" * 70)
    print("DOWNLOAD DFP CVM")
    print("=" * 70)
    print("URL:", url)
    print("Cache:", arquivo_cache)

    ultima_falha = None

    for tentativa in range(1, 6):
        try:
            print(f"Tentativa {tentativa}/5...")

            response = requests.get(
                url,
                timeout=120,
                headers={
                    "User-Agent": "Mozilla/5.0 B3FundamentalistaEngine"
                }
            )

            response.raise_for_status()

            arquivo_cache.write_bytes(response.content)

            print("Download concluído e cache atualizado.")

            return zipfile.ZipFile(
                io.BytesIO(response.content)
            )

        except Exception as e:
            ultima_falha = e
            print(f"Falha na tentativa {tentativa}: {e}")

            if tentativa < 5:
                print("Aguardando 20 segundos para nova tentativa...")
                time.sleep(20)

    if arquivo_cache.exists():
        print("CVM indisponível. Usando último cache válido.")
        return zipfile.ZipFile(arquivo_cache)

    raise Exception(
        f"Falha ao baixar dados da CVM e cache inexistente: {ultima_falha}"
    )


# ============================================================
# LEITURA CSV
# ============================================================

def ler_csv(zip_file, nome_arquivo):
    with zip_file.open(nome_arquivo) as f:
        df = pd.read_csv(
            f,
            sep=";",
            encoding="latin1",
            low_memory=False
        )

    return df


# ============================================================
# CARGA PRINCIPAL
# ============================================================

def carregar_dados_cvm(ano=ANO_DFP):
    zip_file = baixar_zip_cvm(ano)

    arquivos = zip_file.namelist()

    print()
    print("Arquivos encontrados:")

    for arquivo in arquivos:
        print("-", arquivo)

    df_bpa = ler_csv(
        zip_file,
        f"dfp_cia_aberta_BPA_con_{ano}.csv"
    )

    df_bpp = ler_csv(
        zip_file,
        f"dfp_cia_aberta_BPP_con_{ano}.csv"
    )

    df_dre = ler_csv(
        zip_file,
        f"dfp_cia_aberta_DRE_con_{ano}.csv"
    )

    df_dfc = ler_csv(
        zip_file,
        f"dfp_cia_aberta_DFC_MD_con_{ano}.csv"
    )

    print()
    print("=" * 70)
    print("DADOS CVM CARREGADOS")
    print("=" * 70)
    print("BPA:", len(df_bpa))
    print("BPP:", len(df_bpp))
    print("DRE:", len(df_dre))
    print("DFC:", len(df_dfc))

    return {
        "bpa": df_bpa,
        "bpp": df_bpp,
        "dre": df_dre,
        "dfc": df_dfc
    }


if __name__ == "__main__":
    dados = carregar_dados_cvm()
    print(dados["dre"].head())
