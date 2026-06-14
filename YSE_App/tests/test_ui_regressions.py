"""Regression tests for post-merge UI fixes (filter colors, pagination, magnitudes)."""

import os
import unittest
from unittest import mock

from django.core.cache import cache
from django.test import Client, TestCase
from explorer.models import Query

from YSE_App.common.filter_display import (
    band_display_color,
    display_filter_label,
    normalize_filter_name,
    plot_legend_label,
    telescope_display_name,
    telescope_display_symbol,
)
from YSE_App.common.magnitude_format import format_magnitude, format_magnitude_with_error
from YSE_App.models import Transient, UserQuery
from YSE_App.table_utils import MagnitudeColumn, annotate_dashboard_transient_fields
from YSE_App.tests.fixtures_minimal import (
    attach_synthetic_photometry,
    audit_fields,
    create_minimal_transient,
    create_test_user,
)
from YSE_App.views import QUERY_CACHE_VERSION


class FilterDisplayTests(TestCase):
    def test_normalize_r_family_filters(self):
        self.assertEqual(normalize_filter_name('r-ZTF'), 'r')
        self.assertEqual(normalize_filter_name('r-WFT'), 'r')
        self.assertEqual(normalize_filter_name('r'), 'r')
        self.assertEqual(normalize_filter_name('R-Cousins'), 'r')

    def test_r_family_shares_swope_red(self):
        swope_r = band_display_color('r', '#DC143C')
        ztf_r = band_display_color('r-ZTF', None)
        wft_r = band_display_color('r-WFT', None)
        self.assertEqual(swope_r, ztf_r)
        self.assertEqual(swope_r, wft_r)
        self.assertEqual(swope_r, '#DC143C')

    def test_telescope_symbol_groups_ztf(self):
        self.assertEqual(telescope_display_symbol('ZTF-Cam'), 'diamond')
        self.assertEqual(telescope_display_symbol('Unknown'), 'triangle')

    def test_g_atlas_cyan_maps_to_green(self):
        self.assertEqual(normalize_filter_name('cyan-ATLAS'), 'g')
        self.assertEqual(band_display_color('cyan-ATLAS', None), '#008000')

    def test_display_filter_label_shortens_instrument_suffix(self):
        self.assertEqual(display_filter_label('r-ZTF'), 'r')
        self.assertEqual(display_filter_label('g-WFT'), 'g')
        self.assertEqual(display_filter_label('r'), 'r')

    def test_telescope_display_name_shortens_instrument(self):
        self.assertEqual(telescope_display_name('ZTF-Cam', 'ZTF'), 'ZTF')
        self.assertEqual(telescope_display_name('ZTF-Cam', None), 'ZTF')
        self.assertEqual(telescope_display_name(None, '1m-SWOPE'), 'Swope')

    def test_plot_legend_label_telescope_and_filter_separate(self):
        self.assertEqual(
            plot_legend_label('r-ZTF', instrument_name='ZTF-Cam', telescope_name='ZTF'),
            'ZTF r',
        )
        self.assertEqual(
            plot_legend_label('g-WFT', instrument_name='WFT', telescope_name=None),
            'WFT g',
        )


class MagnitudeFormatTests(TestCase):
    def test_two_decimal_places(self):
        self.assertEqual(format_magnitude(18.3248572), '18.32')
        self.assertEqual(format_magnitude(None), '-')

    def test_mag_with_error(self):
        self.assertEqual(format_magnitude_with_error(18.324, 0.0891), '18.32 ± 0.09')


class PersonalDashboardPaginationTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='pdash_pagination_user')
        self.client = Client()
        self.client.force_login(self.user)
        self.transient_names = []
        for i in range(15):
            t = create_minimal_transient(
                self.user,
                name=f'pdash-page-{i:02d}',
                ra=10.0 + i * 0.01,
            )
            self.transient_names.append(t.name)

        names_sql = "', '".join(self.transient_names)
        sql = (
            "SELECT name FROM YSE_App_transient "
            f"WHERE name IN ('{names_sql}') ORDER BY name"
        )
        explorer_query = Query.objects.create(
            title='All transients in YSE PZ',
            sql=sql,
            description='Pagination regression test query',
            snapshot=False,
            created_by_user=self.user,
        )
        self.user_query = UserQuery.objects.create(
            user=self.user,
            query=explorer_query,
            **audit_fields(self.user),
        )
        cache.set(
            f'user_query_{QUERY_CACHE_VERSION}_{self.user_query.id}',
            self.transient_names,
            timeout=3600,
        )

    @mock.patch.dict(os.environ, {'YSE_PERSONAL_DASHBOARD_DEFER': '1'})
    def test_section_fragment_respects_prefixed_page_param(self):
        prefix = self.user_query.query.title.replace(' ', '') + '-'
        page1_url = (
            f'/personaldashboard/section/{self.user_query.id}/'
            f'?{prefix}page=1'
        )
        page2_url = (
            f'/personaldashboard/section/{self.user_query.id}/'
            f'?{prefix}page=2'
        )
        page1 = self.client.get(page1_url)
        page2 = self.client.get(page2_url)
        self.assertEqual(page1.status_code, 200)
        self.assertEqual(page2.status_code, 200)
        body1 = page1.content.decode()
        body2 = page2.content.decode()
        self.assertIn(f'{prefix}page=2', body1)
        self.assertNotEqual(body1, body2)
        names_on_page1 = [n for n in self.transient_names if n in body1]
        names_on_page2 = [n for n in self.transient_names if n in body2]
        self.assertGreater(len(names_on_page1), 0)
        self.assertGreater(len(names_on_page2), 0)
        self.assertLessEqual(len(names_on_page1), 10)
        self.assertLessEqual(len(names_on_page2), 10)
        self.assertEqual(len(set(names_on_page1) & set(names_on_page2)), 0)

    @mock.patch.dict(os.environ, {'YSE_PERSONAL_DASHBOARD_DEFER': '1'})
    def test_deferred_shell_passes_query_string_to_section_loader(self):
        prefix = self.user_query.query.title.replace(' ', '') + '-'
        response = self.client.get(f'/personaldashboard/?{prefix}page=2')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('window.location.search', body)
        self.assertIn('sectionUrl', body)


class MagnitudeColumnTests(TestCase):
    def test_render_formats_to_two_decimals(self):
        col = MagnitudeColumn()
        self.assertEqual(col.render(17.4567), '17.46')

    def test_dashboard_annotation_still_numeric(self):
        user = create_test_user(username='mag_col_user')
        transient = create_minimal_transient(user, name='mag-col-test')
        attach_synthetic_photometry(user, transient, n_points=2)
        row = annotate_dashboard_transient_fields(
            Transient.objects.filter(pk=transient.pk)
        ).first()
        self.assertIsNotNone(row.recent_mag)
