"""Ponto de entrada do Enviador de PDF + XML avulso (.exe ou `python main.py`)."""

import sys

from enviador_pdf_xml.modulo import MODULO
from tcm_ui.avulso import rodar_avulso

if __name__ == "__main__":
    sys.exit(rodar_avulso(MODULO))
