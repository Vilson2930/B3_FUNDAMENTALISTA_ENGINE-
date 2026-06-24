# ============================================================
# cvm_data.py
# B3 FUNDAMENTALISTA ENGINE
# Download e carregamento dos dados oficiais da CVM
# ============================================================

import io
import time
import zipfile
import requests
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

ANO_DFP = 2025

# ============================================================
# DOWNLOAD CVM COM RETENTATIVAS
# ============================================================

def baixar_zip_cvm(ano=ANO_DFP):

    url = (
        f"https://dados.cvm.gov.br/dados/"
        f"CIA_ABERTA/DOC/DFP/DADOS/"
        f"dfp_cia_aberta_{ano}.zip"
    )

    print("=" * 70)
    print("DOWNLOAD DFP CVM")
    print("=" * 70)
    print("URL:", url)

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

            print("Download concluído.")

            return zipfile.ZipFile(
                io.BytesIO(response.content)
            )

        except Exception as e:
            ultima_falha = e
            print(f"Falha na tentativa {tentativa}: {e}")

            if tentativa < 5:
                print("Aguardando 20 segundos para nova tentativa...")
                time.sleep(20)

    raise Exception(
        f"Falha ao baixar dados da CVM após 5 tentativas: {ultima_falha}"
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

# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    dados = carregar_dados_cvm()

    print()
    print("BPA")
    print(dados["bpa"].head())

    print()
    print("DRE")
    print(dados["dre"].head())
