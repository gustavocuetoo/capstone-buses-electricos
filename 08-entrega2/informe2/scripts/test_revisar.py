import unittest

import revisar


class TestTex(unittest.TestCase):
    def test_numero_con_separador_de_miles_es_error(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Se cubren 33.220 corridas.')
        self.assertEqual(len(errores), 1)

    def test_decimal_con_coma_es_error(self):
        errores, _ = revisar.problemas_en_tex('cap', 'El vacío es 16,6 por ciento.')
        self.assertEqual(len(errores), 1)

    def test_macros_y_enteros_simples_pasan(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Usa \\BusesModelo{} buses en 5 sectores y 212 rutas.')
        self.assertEqual(errores, [])

    def test_comentarios_y_marca_literal_no_se_revisan(self):
        texto = '% 33.220 en comentario\nEl año 2.026 %literal\nPorcentaje 10\\% de 3 casos.'
        errores, _ = revisar.problemas_en_tex('cap', texto)
        self.assertEqual(errores, [])

    def test_coordenadas_tikz_no_son_cifras(self):
        texto = '\\begin{tikzpicture}\n\\node at (0,1.5) {A};\n\\end{tikzpicture}'
        errores, _ = revisar.problemas_en_tex('cap', texto)
        self.assertEqual(errores, [])

    def test_viaje_esta_prohibido(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Cada viaje se cubre una vez.')
        self.assertEqual(len(errores), 1)

    def test_restos_de_plantilla_son_error(self):
        errores, _ = revisar.problemas_en_tex('main', '\\section{First Appendix}')
        self.assertEqual(len(errores), 1)

    def test_pendientes_se_informan_aparte(self):
        errores, pendientes = revisar.problemas_en_tex('cap', '\\nocite{*} y [POR COMPLETAR: responsables]')
        self.assertEqual(errores, [])
        self.assertEqual(len(pendientes), 2)


class TestPdf(unittest.TestCase):
    def test_referencias_rotas_y_rotulos_en_ingles(self):
        problemas = revisar.problemas_en_pdf('Ver Tabla ?? y la Figure 2.\nAPPENDIX')
        self.assertEqual(len(problemas), 3)

    def test_pdf_limpio(self):
        self.assertEqual(revisar.problemas_en_pdf('Ver la Tabla 7.1 y la Figura 2.1.'), [])


class TestPaginas(unittest.TestCase):
    TOC = (
        '\\contentsline {chapter}{RESUMEN}{vii}{chapter*.3}%\n'
        '\\contentsline {chapter}{\\numberline {1.}INTRODUCCI\\IeC {\\\'O}N}{1}{chapter.1}%\n'
        '\\contentsline {section}{\\numberline {1.1.}Contexto}{1}{section.1.1}%\n'
        '\\contentsline {chapter}{\\numberline {2.}DESCRIPCI\\IeC {\\\'O}N}{3}{chapter.2}%\n'
        '\\contentsline {chapter}{REFERENCIAS}{8}{chapter*.9}%\n'
    )

    def test_paginas_por_capitulo_hasta_referencias(self):
        paginas = revisar.paginas_por_capitulo(self.TOC)
        self.assertEqual(paginas, {'capitulos': {1: 2, 2: 5}, 'total': 7})

    def test_formato_real_de_pucthesis(self):
        toc = (
            '\\contentsline {chapter}{\\tocchapter {}{}{RESUMEN}}{v}{chapter*.4}%\n'
            '\\contentsline {chapter}{\\tocchapter {}{1}{INTRODUCCIÓN}}{1}{chapter.1}%\n'
            '\\contentsline {chapter}{\\tocchapter {}{2}{DESCRIPCIÓN DETALLADA}}{3}{chapter.2}%\n'
            '\\contentsline {chapter}{\\tocchapter {}{}{REFERENCIAS}}{8}{chapter*.6}%\n'
            '\\contentsline {chapter}{\\tocappendix {}{}{ANEXO}}{14}{appendix*.7}%\n'
        )
        self.assertEqual(revisar.paginas_por_capitulo(toc), {'capitulos': {1: 2, 2: 5}, 'total': 7})

    def test_sin_referencias_es_error(self):
        with self.assertRaises(ValueError):
            revisar.paginas_por_capitulo('\\contentsline {chapter}{\\numberline {1.}A}{1}{chapter.1}%\n')


if __name__ == '__main__':
    unittest.main()
