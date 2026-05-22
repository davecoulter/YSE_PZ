from django.test import SimpleTestCase

from YSE_App.data_utils import getRADecBox


class GetRADecBoxTests(SimpleTestCase):
    def test_square_box_when_dec_size_omitted(self):
        ramin, ramax, decmin, decmax = getRADecBox(180.0, 45.0, size=0.1)
        self.assertAlmostEqual(decmax - decmin, 0.1, places=5)
        self.assertGreater(ramax, ramin)

    def test_dec_size_controls_declination_extent(self):
        ramin, ramax, decmin, decmax = getRADecBox(
            180.0, 45.0, size=0.1, dec_size=0.2
        )
        self.assertAlmostEqual(decmax - decmin, 0.2, places=5)
        self.assertGreater(ramax - ramin, 0.1)
