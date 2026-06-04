"""Phase 0 UI bugfixes (#16–#23)."""

from django.contrib.auth.models import User
from django.test import TestCase

from YSE_App.models import PhotometricBand, Transient, TransientClass, TransientStatus
from YSE_App.serializers.photometric_band_serializers import PhotometricBandSerializer
from YSE_App.table_utils import (
    FollowupTable,
    ObsNightFollowupTable,
    TransientTable,
    stable_order_by,
)
from YSE_App.tests.fixtures_minimal import (
    audit_fields,
    create_test_user,
    ensure_transient_statuses,
)
from YSE_App.view_utils import _phot_data_quality_label


class StableSortTests(TestCase):
    def test_stable_order_by_appends_pk(self):
        qs = Transient.objects.all()
        ordered = stable_order_by(qs, "best_spec_class", True)
        self.assertEqual(list(ordered.query.order_by), ["-best_spec_class", "-pk"])

    def test_order_best_spec_class_uses_pk_tiebreaker(self):
        user = create_test_user("phase0_sort_user")
        spec_class, _ = TransientClass.objects.get_or_create(
            name="phase0-test-class",
            defaults=audit_fields(user),
        )
        from YSE_App.tests.fixtures_minimal import create_minimal_transient

        ids = []
        for i in range(3):
            t = create_minimal_transient(
                user,
                name=f"phase0sort{i:02d}",
                status_name="Watch",
            )
            t.best_spec_class = spec_class
            t.save(update_fields=["best_spec_class"])
            ids.append(t.pk)

        qs = Transient.objects.filter(pk__in=ids)
        table = TransientTable(qs)
        ordered, handled = table.order_best_spec_class(qs, False)
        self.assertTrue(handled)
        self.assertEqual(list(ordered.query.order_by), ["best_spec_class", "pk"])


class FollowupTableSortTests(TestCase):
    def test_obs_night_name_column_orders_transient_name(self):
        col = ObsNightFollowupTable.base_columns["name_string"]
        self.assertEqual(col.order_by, ("transient__name",))

    def test_followup_table_name_column_orders_transient_name(self):
        col = FollowupTable.base_columns["name_string"]
        self.assertEqual(col.order_by, ("transient__name",))


class PhotometricBandSerializerTests(TestCase):
    def test_update_sets_disp_symbol_not_disp_color(self):
        user = create_test_user("phase0_band_user")
        from YSE_App.tests.fixtures_minimal import create_instrument_stack

        _, instrument, band = create_instrument_stack(user, obs_group_name="phase0-band")
        band.disp_color = "#111111"
        band.disp_symbol = "circle"
        band.save()
        serializer = PhotometricBandSerializer(
            band,
            data={
                "disp_color": "#222222",
                "disp_symbol": "square",
                "instrument": f"http://testserver/api/instruments/{instrument.pk}/",
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save(modified_by=user)
        self.assertEqual(updated.disp_color, "#222222")
        self.assertEqual(updated.disp_symbol, "square")


class TransientTagSerializerTests(TestCase):
    def test_patch_same_tags_is_noop(self):
        user = create_test_user("phase0_tag_user")
        from YSE_App.models import TransientTag

        audit = audit_fields(user)
        tag, _ = TransientTag.objects.get_or_create(name="phase0-paper", defaults=audit)
        statuses = ensure_transient_statuses(user)
        from YSE_App.tests.fixtures_minimal import create_minimal_transient
        transient = create_minimal_transient(user, name="phase0tag01", status_name="New")
        transient.tags.add(tag)
        existing = set(transient.tags.values_list("id", flat=True))
        self.assertIn(tag.pk, existing)
        # Re-adding the same tag set must not clear tags (regression for #214).
        transient.tags.add(tag)
        self.assertEqual(set(transient.tags.values_list("id", flat=True)), existing)


class BokehStaticTests(TestCase):
    def test_bokeh_min_js_exists(self):
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "static" / "YSE_App" / "bokeh-2.4.2.min.js"
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 100_000)


class PhotDataQualityLabelTests(TestCase):
    def test_label_good_when_no_flags(self):
        user = create_test_user("phase0_dq_user")
        from YSE_App.tests.fixtures_minimal import attach_synthetic_photometry, create_minimal_transient

        transient = create_minimal_transient(user, name="phase0dq01")
        phot = attach_synthetic_photometry(user, transient)
        point = phot.transientphotdata_set.first()
        self.assertEqual(_phot_data_quality_label(point), "Good")
