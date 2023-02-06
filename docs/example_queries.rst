.. _example_queries:

******************************
Example SQL Queries for YSE-PZ
******************************

Below we include a few example queries for YSE-PZ.  For a complete picture of the available tables and columns that can be used in queries like the ones below, go to http://127.0.0.1:8000/explorer/new/, and select the show schema button.

1. Every spectroscopically classified SN Ia in the last 30 days
===============================================================
::
   
  SELECT t.name
  FROM YSE_App_transient t
  WHERE t.TNS_spec_class = 'SN Ia' AND DATEDIFF(CURDATE(),t.disc_date) < 30

To include peculiar SNe Ia, the easiest way is to modify the :code:`WHERE` statement to
:code:`t.TNS_spec_class LIKE 'SN Ia%'`.

  
2. Every SN that has been tagged as :code:`Young`
=================================================
::

  SELECT t.name
  FROM YSE_App_transient t
  INNER JOIN YSE_App_transient_tags tt ON tt.transient_id = t.id
  INNER JOIN YSE_App_transienttag tg ON tg.id = tt.transienttag_id
  WHERE tg.name = 'Young'

  
3. Every SN where the most recent magnitude is brighter than 18
===============================================================
::

  SELECT t.name, pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND pd.mag < 18 AND
   pd.id = (
         SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
         WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
         ORDER BY pd2.obs_date DESC
         LIMIT 1
     )

4. Every SN where the peak magnitude is brighter than 18
========================================================
::
   
   SELECT DISTINCT t.name, pd.mag, t.ra, t.dec
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p, YSE_App_transient_tags tt, YSE_App_transienttag tg
   WHERE pd.photometry_id = p.id AND pd.mag < 18.6 AND
   pd.id = (
      SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
      WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND
      ISNULL(pd2.mag) = False
      ORDER BY pd2.mag ASC
      LIMIT 1
   )
   LIMIT 10

     
5. All transients with host galaxy data
=======================================
::
   
  SELECT t.name, t.ra, t.dec, t.disc_date, t.redshift,
  t.TNS_spec_class AS 'classification',
  h.ra AS host_RA, h.dec AS host_Dec, h.name as host_name,
  h.redshift AS host_z

  FROM YSE_App_transient t
  INNER JOIN YSE_App_host h ON h.id = t.host_id

  /*Query from Alex Gagliano*/


6. Transients Observed (S/N > 3) by PS1 or PS2
==============================================
::
   
  SELECT DISTINCT t.name,
		  t.ra,
		  t.dec
  FROM YSE_App_transient t
  WHERE t.id IN
  (SELECT DISTINCT t.id
  FROM YSE_App_transient t
  INNER JOIN YSE_App_transientphotometry tp ON t.id = tp.transient_id
  INNER JOIN YSE_App_transientphotdata tpd ON tp.id = tpd.photometry_id
  INNER JOIN YSE_App_instrument i ON i.id = tp.instrument_id
  WHERE (i.name = "GPC1" or i.name = 'GPC2')
  AND tpd.flux/tpd.flux_err > 3
  GROUP BY t.id
  HAVING count(t.id) >= 1)


7. Every Instrument/Telescope/Observatory in YSE_PZ
===================================================
::
   
   SELECT i.name as instrument_name,
	  t.name as telescope_name,
	  o.name as observatory_name
   FROM YSE_App_instrument i, YSE_App_telescope t, YSE_App_observatory o
   WHERE i.telescope_id = t.id AND t.observatory_id = o.id


8. All Transients with Status of "FollowupRequested"
====================================================
::
   
   SELECT t.name,
	  t.ra,
	  t.dec,
	  ts.name,
	  t.disc_date AS disc_date,

   FROM YSE_App_transient t
   INNER JOIN YSE_App_transientstatus ts ON ts.id = t.status_id
   WHERE ts.name = 'FollowupRequested'

   /*Query from Cesar Rojas-Bravo*/
   
You can use :code:`OR` syntax to include multiple statuses in the
query (:code:`ts.name = 'FollowupRequested' or ts.name = 'Following'`)

9. Coordinate Query: All Transients Near Virgo
==============================================
::
   
   SELECT t.name
   FROM YSE_App_transient t

   WHERE
   /* using approx Virgo coords from YSE observations */
   t.ra > 187.7059-1.65 AND t.ra < 187.7059+1.65 AND
   t.dec > 12.391-1.65 AND t.dec < 12.391+1.65


10.  Every Transient within 30 arcsec of another Transient
==========================================================
::
   
   SELECT DISTINCT t.name as first_transient, t2.name as second_transient
   FROM YSE_App_transient t, YSE_App_transient t2

   WHERE t2.id = (
   SELECT t2.id
   FROM YSE_App_transient t2
   WHERE t2.ra > t.ra - 0.008/COS(t.dec*0.017) AND t2.ra < t.ra + 0.008/COS(t.dec*0.017) AND
   t2.dec > t.dec - 0.008 AND t2.dec < t.dec + 0.008 AND t.name != t2.name
   LIMIT 1)
   LIMIT 10
   /*runs pretty slowly, adjust limit as needed*/


11.  Survey Observations
========================
::
   
   SELECT f.field_id,
	  f.ra_cen,
	  f.dec_cen,
	  f.width_deg,
	  s.obs_mjd,
	  s.pos_angle_deg,
	  s.airmass,
	  s.image_id,
	  s.survey_field_id,
	  s.mag_lim
   FROM YSE_App_surveyfield f
   JOIN YSE_App_surveyobservation s ON s.survey_field_id = f.id
   WHERE s.obs_mjd != 'None'
   /* Query from Chris Carroll, Vivienne Baldassare */


12. Transients Scheduled for Follow-up on Keck in the last two weeks
====================================================================
::
   
   SELECT t.name
   FROM YSE_App_transient t
   JOIN YSE_App_transientfollowup tf ON t.id = tf.transient_id
   JOIN YSE_App_classicalresource rc ON rc.id = tf.classical_resource_id
   JOIN YSE_App_telescope tl ON tl.id = rc.telescope_id
   
   WHERE tl.name LIKE 'Keck%' and DATEDIFF(CURDATE(),tf.valid_start) < 14


13. Spectroscopic Observations for Transients from 2021
=======================================================
::
   
   SELECT t.name,
          t.ra AS transient_RA,
          t.dec AS transient_Dec,
          t.non_detect_date AS non_detect_date,
          t.disc_date AS disc_date,
          spec.obs_date AS spec_date,
          DATEDIFF(spec.obs_date, disc_date) AS spec_epoch,
          t.TNS_spec_class AS spec_class,
          t.redshift AS transient_z,
          t.non_detect_limit,
          t.mw_ebv,
          spec.obs_date

   FROM YSE_App_transient t, YSE_App_transientspectrum spec

   WHERE spec.transient_id = t.id
   AND t.name LIKE "2021%"
   /* Query from Kaew Tinyanont */


14. Every SN within 40 kpc of a z < 0.01 host galaxy
====================================================
::

  SELECT t.name,
       t.ra AS transient_RA,
       t.`dec` AS transient_Dec,
       t.TNS_spec_class AS spec_class,
       t.redshift AS transient_z,
       h.ra AS host_RA,
       h.`dec` AS host_Dec,
       h.redshift AS host_z,
       DEGREES(ACOS(SIN(RADIANS(t.`dec`))*SIN(RADIANS(h.`dec`)) + COS(RADIANS(t.`dec`))*COS(RADIANS(h.`dec`))*COS(RADIANS(ABS(t.ra - h.ra)))))*3600 AS AngSepArcSec,
       (3e+5*COALESCE(t.redshift, h.redshift)/73) AS LuminosityDistanceMpc,
       (3e+5*COALESCE(t.redshift, h.redshift)/73)/POW((1.0 + COALESCE(t.redshift, h.redshift)), 2) AS AngularDiameterDistanceMpc,
       (ACOS(SIN(RADIANS(t.`dec`))*SIN(RADIANS(h.`dec`)) + COS(RADIANS(t.`dec`))*COS(RADIANS(h.`dec`))*COS(RADIANS(ABS(t.ra - h.ra))))*(3e+5*COALESCE(t.redshift, h.redshift)/73)/POW((1.0 + COALESCE(t.redshift, h.redshift)), 2)*1000) AS ProjectedDistKpc
  FROM YSE_App_transient t
  INNER JOIN YSE_App_host h ON h.id = t.host_id
  WHERE t.host_id IS NOT NULL
  AND (t.redshift
  OR h.redshift) IS NOT NULL
  AND COALESCE(t.redshift, h.redshift) > 0.028
  AND COALESCE(t.redshift, h.redshift) < 0.032
  AND t.TNS_spec_class = "SN Ia"
  AND (ACOS(SIN(RADIANS(t.`dec`))*SIN(RADIANS(h.`dec`)) + COS(RADIANS(t.`dec`))*COS(RADIANS(h.`dec`))*COS(RADIANS(ABS(t.ra - h.ra))))*(3e+5*COALESCE(t.redshift, h.redshift)/73)/POW((1.0 + COALESCE(t.redshift, h.redshift)), 2)*1000) < 40;

  /*Query from Dave Coulter*/

