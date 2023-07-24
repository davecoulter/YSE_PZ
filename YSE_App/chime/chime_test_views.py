""" Test views for CHIME. """""
from django.shortcuts import render

from YSE_App import table_utils
from YSE_App.models import Host, Transient

from IPython import embed

def candidatesview(request):
    #request=None
    # Grab the candidates
    frb_name = 'FRB20300714A'
    itransient = Transient.objects.get(name=frb_name)
    candidates = Host.objects.filter(transient_candidates=itransient.id)

    # Filter
    candidatefilter = table_utils.CandidatesFilter(
            None, queryset=candidates)#,prefix=t)
    # Make the table
    candidate_table = table_utils.CandidatesTable(candidatefilter.qs)

    # Proceed?!
    #RequestConfig(request, paginate={'per_page': 10}).configure(candidate_table)
    candidate_table_context = (candidate_table,candidates,candidatefilter)
    context = {
        'candidates': candidate_table_context,
    }

    return render(request, 'YSE_App/candidates.html', context)