Adding Forms to the YSE-PZ Front End
************************************

At Charlie's request, I wanted to document a brief example of how
to add front-end utilities to the YSE-PZ pages.  In this case, I'm
going to write a web form that sets up an automated way to trigger
LCOGT or SOAR spectroscopic followup via their respective APIs.

This procedure can be generalized to other forms, functionality,
user input, etc.  The main toolset in this tutorial is how to use
Django forms models.  Usually Django forms are tied to a YSE-PZ
object itself, though we won't really be saving any data to SQL
during this procedure.

Writing a YSE-PZ Form
=====================

With some small exceptions, YSE-PZ forms are rendered using the
:code:`forms.py` script in the :code:`YSE_App/` directory.  In this
case we'll tie the form to the :code:`TransientFollowup` model.
Starting with the minimum::

  from django.forms import ModelForm
  from django import forms
  
  class LCOGTSpectrumRequest(ModelForm):
      class Meta:
          model = TransientFollowup
          fields =()

In this case we won't really be using the fields from the
:code:`TransientFollowup` model directly, but we'll add our
own fields to the form.  For LCOGT, we need to ask the user for
the desired exposure time, whether they'd like a FLOYDS or Goodman
spectrum, and what the desired date range would be.  We can do this
using the django forms module, which will set the fields that get
automatically rendered in the form::

  class AutomatedSpectrumRequest(ModelForm):

	spec_instruments = ['FLOYDS-N','FLOYDS-S','Goodman']
	instrument = forms.ModelChoiceField(Instrument.objects.filter(Q(name__in=spec_instruments)))
	exp_time = forms.IntegerField(initial=1800) # 1800s seems like a reasonable default
	spectrum_valid_start = forms.DateTimeField()
	spectrum_valid_stop = forms.DateTimeField()
	
	class Meta:
		model = TransientFollowup
		fields =('transient',)

:code:`spectrum_valid_start` and :code:`spectrum_valid_stop` will be written to the :code:`valid_start`
and :code:`valid_stop` fields in in the TransientFollowup model, and :code:`transient` is already part of
the TransientFollowup model, so we can add a few necessary fields
and then use this form to build a TransientFollowup entry.
	  
Starting a YSE-PZ Form View
===========================

Now for the form "view", which I will primarily use to save the form data from the frontend and
perform actions on the YSE-PZ backend.  First, the basics::

  class AddAutomatedSpectrumRequestFormView(FormView):
	form_class = AutomatedSpectrumRequest
	template_name = 'YSE_App/form_snippets/spectrum_request_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
	    response = super(AddAutomatedSpectrumRequestFormView, self).form_invalid(form)
	    if self.request.is_ajax():
	        return JsonResponse(form.errors, status=400)
            else:
	        return response

	def form_valid(self, form):
	    response = super(AddTransientFollowupFormView, self).form_valid(form)
	    if self.request.is_ajax():
	        pass
		    
This sets up the basic form defaults, including the form class object, the name
of the template form we're about to create, and the error function for if the
form is invalid.  If the form is valid, and verifying that the request is passed
by AJAX code on the frontend, then we will execut the necessary code.

Finally, we need to add the form view to :code:`urls.py`.  You can add the following
to the :code:`urlpatterns` list.::

  url(r'^automated_spectrum_request/', AddAutomatedSpectrumRequestFormView.as_view(), name='automated_spectrum_request'),

Rendering the Form on the YSE-PZ FrontEnd
=========================================

Now let's write the Django template code to render the form.  I usually split this
into some basic HTML code that gets passed to the main page, and then a separate
HTML script in the :code:`form_snippets` directory to render the form itself.

But first, we need to make sure the function that is generating the frontend view
includes an instance of the form.  In :code:`view.py`, I'm going to edit the
transient :code:`detail` page to include our new form, which is the function
:code:`def transient_detail(request, slug)` (you can see this in the :code:`urls.py`
script).

At the top, I'm going to add a line::

  automated_spectrum_form = AutomatedSpectrumRequest()

and at the bottom, I'll include this variable in the context that
gets rendered in the view.::

  context['automated_spectrum_form'] = automated_spectrum_form

Writing the Django HTML
-----------------------
  
Now, to edit the HTML itself.  You can see in the :code:`transient_detail`
function that the template being rendered is :code:`YSE_App/transient_detail.html`.
These paths are relative to the :code:`YSE_App/templates` directory.  As we are
creating a new TransientFollowup object, this form should be in the `followup_tab`,
where I will create a new row to contain it::

  <div class="row">
      <div class="col-xs-6">
          <input type="hidden" id="transient_pk" value="{{ transient.id }}"/>
          {% include "YSE_App/form_snippets/automated_spectrum_form.html" with form=automated_spectrum_form %}
      </div>
  </div>

Without going into a full-on Django tutorial, the curly brackets
and percent signs indicate Django instructions, while the rest is
HTML.  This will pass our form variable (:code:`automated_spectrum_form`)
to the form snippet that we're about to write.

In this form snippet, we just need to enable `django-widget-tweaks <https://github.com/jazzband/django-widget-tweaks>_` to allow
the form to easily render (slightly easier than just doing it in HTML),
and we need to add all the fields in our original :code:`forms.py` class.::

  {% load widget_tweaks %}

  {% block content %}
   <div class="box box-primary box-solid collapsed-box"> <!--collapsed-box-->
       <div class="box-header with-border">
	   <button id="automated_spectrum_request_btn" type="button" class="btn btn-box-tool" data-widget="collapse" style="height: 30px;"><h3 class="box-title">Automated Spectrum Request</h3></button>
	   <div class="box-tools pull-right">
	       <button id="automated_spectrum_request_btn" type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button>
	   </div>
       </div>
       <div class="box-body">
	   <form id="automated_spectrum_request" action="{% url 'automated_spectrum_request' %}" method="post">
	       {% csrf_token %}
	       {% for hidden_field in form.hidden_fields %}
		   {{ hidden_field }}
	       {% endfor %}
	       <div class="col-xs-6">
		   <div class="form-group">
		       <label>Instrument</label>
		       {% render_field form.instrument class+="form-control select2" %}
		   </div>
	       </div>
	       <div class="col-xs-6">
		   <div class="form-group">
		       <label>Exposure Time</label>
		       {% render_field form.exp_time class+="form-control select2" %}
		   </div>
	       </div>
	       <div class="col-xs-12">
		   <div class="form-group">
		       <label>Date Range</label>
			   <div class="input-group">
			       <div class="input-group-addon">
				   <i class="fa fa-clock-o"></i>
			       </div>
			       <input type="text" class="form-control pull-right" id="automated_spectrum_date_range">
			   </div>
			   <input type="hidden" id="spectrum_valid_start" name="spectrum_valid_start">
			   <input type="hidden" id="spectrum_valid_stop" name="spectrum_valid_stop">
		      </div>
		 </div>

		 <div class="col-xs-12">
		     <div class="form-group">
			  <br>
			  <button type="submit" class="btn btn-block btn-primary btn-lg">Submit</button>
		      </div>
		 </div>
	    </form>
	</div>
   </div>
  {% endblock %}

Without going into the details here, this uses a combination of HTML and
django-widget-tweaks to render your form field.

Writing the JS instructions
---------------------------

Back on the :code:`transient_detail.html` page, we need to add some scripting in the
:code:`{% block scripts %}` section so that the form gets sent to our view.  This does require a
few dependencies that have already been added to the detail page.

Here's the simple function that will do most of the work, pulling from the labeled form ID and adding
in the transient primary key so that the view will automatically know which transient to
associate the TransientFollowup entry with.  We could be fancier here, but for now I'm just
going to see if the JSON data contains any errors that we need to alert the user about.  If not, we
will reload the page and our new followup request will be added::

  <script src="{% static 'YSE_App/bower_components/bootstrap-timepicker/js/bootstrap-timepicker.js' %}"></script>
  <script>
  $('#automated_spectrum_request').on('submit', function(event){
        event.preventDefault();
        automated_spectrum_request();
      });

  function automated_spectrum_request() {
    // Grab the form, and associate it with the current transient detail page
    var data = $('#automated_spectrum_request').serialize()
    var transient_id = $('#transient_pk').val()
    data = (data + "&transient=" + transient_id)
    //alert(data)
    $.ajax({
      url : "{% url 'automated_spectrum_request' %}", // the endpoint
      type : "POST", // http method
      data : data, // data sent with the post request

      // handle a successful response
      success : function(json) {
	var errors = json.data["errors"]		
	// Construct HTML to append container
	if (errors){
	  alert(errors)
	} else {
	  location.reload();
	} 
      },

      // handle a non-successful response
      error : function(xhr,errmsg,err) {
	alert(xhr.status + ": " + xhr.responseText);
      }
      });
    }
    </script>

Then, between the scripts tags we need to render the calendars so that
the user can select the dates in which the request is valid.::

  
  $('#automated_spectrum_date_range').daterangepicker({ 
	  timePicker24Hour: true,
	  timePicker: true, 
	  timePickerIncrement: 1, 
	  format: 'MM/DD/YYYY HH:mm', 
	  locale: {
		  format: 'MM/DD/YYYY HH:mm'
	  } 
  });

  fdr_spec_picker = $('#automated_spectrum_date_range').data('daterangepicker')
  $('#spectrum_valid_start').val(fdr_spec_picker.startDate.format("YYYY-MM-DD HH:mm:00"))
  $('#spectrum_valid_stop').val(fdr_spec_picker.endDate.format("YYYY-MM-DD HH:mm:00"))
  $('#automated_spectrum_date_range').on('apply.daterangepicker', function(ev, picker) {
	  $('#spectrum_valid_start').val(picker.startDate.format("YYYY-MM-DD HH:mm:00"))
	  $('#spectrum_valid_stop').val(picker.endDate.format("YYYY-MM-DD HH:mm:00"))
  });

Last but not least, we need to make sure the form has a valid CSRF token::

  var csrftoken = getCookie('csrftoken');

  /*
  The functions below will create a header with csrftoken
  */

  function csrfSafeMethod(method) {
	  // these HTTP methods do not require CSRF protection
	  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  function sameOrigin(url) {
	  // test that a given url is a same-origin URL
	  // url could be relative or scheme relative or absolute
	  var host = document.location.host; // host + port
	  var protocol = document.location.protocol;
	  var sr_origin = '//' + host;
	  var origin = protocol + sr_origin;
	  // Allow absolute or scheme relative URLs to same origin
	  return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
	  (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
		  // or any other URL that isn't scheme relative or absolute i.e relative.
		  !(/^(\/\/|http:|https:).*/.test(url));
	  }

	  $.ajaxSetup({
		  beforeSend: function(xhr, settings) {
			  if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
			  // Send the token to same-origin, relative URLs only.
			  // Send the token only if the method warrants CSRF protection
			  // Using the CSRFToken value acquired earlier
			  xhr.setRequestHeader("X-CSRFToken", csrftoken);
			  }
		  }
	  });
  });

Finishing the YSE-PZ Form View
==============================
  
Okay!  We're almost there.  Now we need to use the data returned by the
user to create a TransientFollowup object, and then use Charlie's code to
ping the LCOGT or SOAR API.

Here's the full view::

  class AddAutomatedSpectrumRequestFormView(FormView):
	form_class = AutomatedSpectrumRequest
	template_name = 'YSE_App/form_snippets/spectrum_request_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddAutomatedSpectrumRequestFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddAutomatedSpectrumRequestFormView, self).form_valid(form)
		if self.request.is_ajax():
			tfdict = {}
			
			# some hard-coded logic
			if 'goodman' in form.cleaned_data['instrument'].name.lower():
				resource = ClassicalResource.objects.filter(telescope__name=form.cleaned_data['instrument'].telescope).\
					filter(principal_investigator__name='Dimitriadis')
			else:
				resource = ToOResource.objects.filter(telescope__name=form.cleaned_data['instrument'].telescope) #.\
					#filter(principal_investigator__name='Kilpatrick')
				
			# make sure the dates line up, with a +/-1 day window to make life easier
			resource = resource.filter(Q(begin_date_valid__lt=form.cleaned_data['spectrum_valid_start']+datetime.timedelta(1)) &
									   Q(end_date_valid__gt=form.cleaned_data['spectrum_valid_stop']-datetime.timedelta(1)))

			if not len(resource):
				data_dict = {'errors':'could not find a matching resource, make sure the dates are valid and the program is still active!',
							 'errorflag':1}
				data = {
					'data':data_dict,
					'message': "Successfully submitted form data.",
				}
				return JsonResponse(data)
			else:
				resource = resource[0]
			
			status = FollowupStatus.objects.get(name='Requested')

			if 'goodman' in form.cleaned_data['instrument'].name.lower():
				tf = TransientFollowup(status=status,valid_start=form.cleaned_data['spectrum_valid_start'],
									   valid_stop=form.cleaned_data['spectrum_valid_stop'],classical_resource=resource,
									   transient=form.cleaned_data['transient'],created_by=self.request.user,modified_by=self.request.user)
			else:
				tf = TransientFollowup(status=status,valid_start=form.cleaned_data['spectrum_valid_start'],
									   valid_stop=form.cleaned_data['spectrum_valid_stop'],too_resource=resource,
									   transient=form.cleaned_data['transient'],created_by=self.request.user,modified_by=self.request.user)
			tf.save()

			# now charlie's code
			lcogt.main(
				 tf.transient.name,tf.transient.ra,tf.transient.dec,form.cleaned_data['exp_time'],
				 form.cleaned_data['instrument'].telescope.name)

			data_dict = {'errors':'',
						 'errorflag':0}
			data = {
				'data':data_dict,
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

Final Thoughts
==============

Okay!  I didn't really explain everything, but this basic procedure can be
used to build any form you want and trigger some action on the backend.  There
are simpler ways depending on what you want to do, but this template is a
good way to proceed especially if you need to add new entries to the database.
